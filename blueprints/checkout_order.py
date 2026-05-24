from flask import Blueprint, request, session, jsonify
import sys
import os
from decimal import Decimal
from datetime import datetime

# Add the parent directory to the path to import db_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.supabase_helper import *
from blueprints.shipping_fee import (
    calculate_fee,
    get_address_by_id,
    get_seller_default_address,
    DEFAULT_SHIPPING_FEE,
)

checkout_order_bp = Blueprint('checkout_order', __name__)

@checkout_order_bp.route('/place_order', methods=['POST'])
def place_order():
    # Check if user is logged in
    if 'user_id' not in session or not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        
        # Get required data
        cart_ids = data.get('cart_ids', [])
        address_id = data.get('address_id')
        subtotal = Decimal(str(data.get('subtotal', 0)))
        shipping_fee = Decimal(str(data.get('shipping_fee', 0)))
        discount_amount = Decimal(str(data.get('discount_amount', 0)))
        total_amount = Decimal(str(data.get('total_amount', 0)))
        voucher_type = data.get('voucher_type')
        buyer_voucher_id = data.get('voucher_id')
        
        # Check if free shipping voucher is applied
        is_free_shipping = (voucher_type == 'free_shipping')
        
        if not cart_ids or not address_id:
            return jsonify({'success': False, 'message': 'Missing required data'}), 400
        
        supabase = get_supabase()
        if not supabase:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            # Get buyer_id
            buyer = get_buyer_by_user_id(session['user_id'])
            
            if not buyer:
                return jsonify({'success': False, 'message': 'Buyer account not found'}), 404
            
            buyer_id = buyer['buyer_id']
            
            # Get actual voucher_id from buyer_voucher_id
            print(f"VOUCHER DEBUG:")
            print(f"  voucher_type: {voucher_type}")
            print(f"  buyer_voucher_id: {buyer_voucher_id}")
            
            actual_voucher_id = None
            if buyer_voucher_id:
                voucher_response = supabase.table('buyer_vouchers').select('voucher_id').eq('buyer_voucher_id', buyer_voucher_id).eq('buyer_id', buyer_id).execute()
                if voucher_response.data:
                    actual_voucher_id = voucher_response.data[0]['voucher_id']
                    print(f"  Found voucher_id: {actual_voucher_id}")
            
            voucher_id = actual_voucher_id
            
            # Get cart items with variant information and stock
            cart_response = supabase.table('cart').select('''
                cart_id,
                product_id,
                quantity,
                variant_id,
                products (
                    product_name,
                    materials,
                    price,
                    seller_id
                ),
                product_variants (
                    color,
                    size,
                    stock_quantity
                )
            ''').in_('cart_id', cart_ids).execute()
            
            if not cart_response.data:
                return jsonify({'success': False, 'message': 'No items found'}), 404

            # Fallback for Railway: nested `products(...)` and `product_variants(...)`
            # joins occasionally come back empty on production. When that happens
            # checkout fails because seller_id and stock can't be read. Backfill
            # via direct id lookups so order placement still succeeds.
            product_ids_for_lookup = list({i['product_id'] for i in cart_response.data if i.get('product_id')})
            variant_ids_for_lookup = list({i['variant_id'] for i in cart_response.data if i.get('variant_id')})

            products_by_id = {}
            if product_ids_for_lookup:
                try:
                    p_resp = supabase.table('products').select(
                        'product_id, product_name, materials, price, seller_id'
                    ).in_('product_id', product_ids_for_lookup).execute()
                    if p_resp.data:
                        products_by_id = {p['product_id']: p for p in p_resp.data}
                except Exception as fb_err:
                    print(f"⚠️ Order placement product fallback fetch failed: {fb_err}")

            variants_by_id = {}
            if variant_ids_for_lookup:
                try:
                    v_resp = supabase.table('product_variants').select(
                        'variant_id, color, size, stock_quantity'
                    ).in_('variant_id', variant_ids_for_lookup).execute()
                    if v_resp.data:
                        variants_by_id = {v['variant_id']: v for v in v_resp.data}
                except Exception as fb_err:
                    print(f"⚠️ Order placement variant fallback fetch failed: {fb_err}")

            for item in cart_response.data:
                if not item.get('products') and item.get('product_id'):
                    item['products'] = products_by_id.get(item['product_id'], {})
                if not item.get('product_variants') and item.get('variant_id'):
                    item['product_variants'] = variants_by_id.get(item['variant_id'], {})

            # Flatten cart items
            cart_items = []
            for item in cart_response.data:
                product = item.get('products', {})
                variant = item.get('product_variants', {})
                
                cart_items.append({
                    'cart_id': item['cart_id'],
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'variant_id': item['variant_id'],
                    'product_name': product.get('product_name'),
                    'materials': product.get('materials'),
                    'price': product.get('price'),
                    'seller_id': product.get('seller_id'),
                    'variant_color': variant.get('color') if variant else None,
                    'variant_size': variant.get('size') if variant else None,
                    'variant_stock': variant.get('stock_quantity') if variant else None
                })
            
            # Validate stock availability
            for item in cart_items:
                if not item.get('variant_id'):
                    return jsonify({'success': False, 'message': f"Please select a variant for {item['product_name']}."}), 400
                
                if item.get('variant_stock') is None:
                    return jsonify({'success': False, 'message': f"Variant for {item['product_name']} is no longer available."}), 400
                
                if item['variant_stock'] <= 0:
                    return jsonify({'success': False, 'message': f"{item['product_name']} is out of stock."}), 400
                
                if item['quantity'] > item['variant_stock']:
                    return jsonify({'success': False, 'message': f"Insufficient stock for {item['product_name']}."}), 400
            
            # Group items by seller
            from collections import defaultdict
            seller_items = defaultdict(list)
            for item in cart_items:
                seller_items[item['seller_id']].append(item)
            
            # Get starting order number
            current_year = datetime.now().year
            # Use startswith filter instead of like/ilike
            last_order_response = supabase.table('orders').select('order_number').ilike('order_number', f'VEL-{current_year}-*').order('order_id', desc=True).limit(1).execute()
            
            if last_order_response.data:
                try:
                    last_num = int(last_order_response.data[0]['order_number'].split('-')[-1])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            
            # Resolve buyer's address once for tier-based shipping fee
            buyer_address_record = get_address_by_id(supabase, address_id) or {}

            # Compute per-seller tier shipping fees authoritatively on the server.
            # We do not trust the client-supplied shipping_fee.
            seller_fee_map = {}
            for seller_id in seller_items.keys():
                seller_addr = get_seller_default_address(supabase, seller_id) or {}
                fee_value, tier = calculate_fee(buyer_address_record, seller_addr)
                seller_fee_map[seller_id] = {
                    'fee': Decimal(str(fee_value)),
                    'tier': tier,
                }

            total_actual_shipping = sum(
                entry['fee'] for entry in seller_fee_map.values()
            ) or Decimal('0')

            # Distribute discount evenly across sellers (existing behaviour)
            num_sellers = len(seller_items)

            # Create orders for each seller
            order_ids = []

            for seller_id, items in seller_items.items():
                seller_subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in items)
                seller_actual_shipping = seller_fee_map[seller_id]['fee']
                # If buyer has free_shipping voucher, the buyer pays nothing for
                # shipping; the platform absorbs the actual delivery fee.
                seller_shipping = Decimal('0') if is_free_shipping else seller_actual_shipping
                seller_discount = discount_amount / num_sellers
                commission_amount = seller_subtotal * Decimal('0.05')
                seller_total = seller_subtotal + seller_shipping - seller_discount
                
                order_number = f'VEL-{current_year}-{next_num:04d}'
                next_num += 1
                
                # Insert order
                order_data = {
                    'order_number': order_number,
                    'buyer_id': buyer_id,
                    'seller_id': seller_id,
                    'address_id': address_id,
                    'subtotal': float(seller_subtotal),
                    'shipping_fee': float(seller_shipping),
                    'discount_amount': float(seller_discount),
                    'total_amount': float(seller_total),
                    'commission_amount': float(commission_amount),
                    'voucher_id': voucher_id,
                    'order_status': 'pending'
                }
                
                order_response = supabase.table('orders').insert(order_data).execute()
                if not order_response.data:
                    raise Exception("Failed to create order")
                
                order_id = order_response.data[0]['order_id']
                order_ids.append(order_id)
                
                # Get seller address from addresses table
                seller_address_response = supabase.table('addresses').select('full_address').eq('user_type', 'seller').eq('user_ref_id', seller_id).eq('is_default', True).execute()
                
                if seller_address_response.data:
                    pickup_address = seller_address_response.data[0]['full_address']
                else:
                    # Fallback to shop name if no address found
                    seller_response = supabase.table('sellers').select('shop_name').eq('seller_id', seller_id).execute()
                    pickup_address = seller_response.data[0]['shop_name'] if seller_response.data else 'N/A'
                
                # Get buyer address
                address_response = supabase.table('addresses').select('full_address').eq('address_id', address_id).execute()
                delivery_address = address_response.data[0]['full_address'] if address_response.data else 'N/A'
                
                # Calculate delivery fee — use the per-seller tier-based fee.
                # The rider always gets paid the actual delivery fee. When the
                # buyer used a free_shipping voucher, the platform absorbs it.
                actual_delivery_fee = seller_actual_shipping
                
                # Create delivery record with NULL status (seller needs to click "Prepare Package" first)
                delivery_data = {
                    'order_id': order_id,
                    'pickup_address': pickup_address,
                    'delivery_address': delivery_address,
                    'delivery_fee': float(actual_delivery_fee),
                    'paid_by_platform': is_free_shipping,
                    'status': None  # NULL status - seller must click "Prepare Package" first
                }
                supabase.table('deliveries').insert(delivery_data).execute()
                
                # Insert order items and update stock
                for item in items:
                    item_subtotal = Decimal(str(item['price'])) * item['quantity']
                    
                    order_item_data = {
                        'order_id': order_id,
                        'product_id': item['product_id'],
                        'product_name': item['product_name'],
                        'materials': item['materials'],
                        'variant_color': item.get('variant_color'),
                        'variant_size': item.get('variant_size'),
                        'quantity': item['quantity'],
                        'unit_price': float(item['price']),
                        'subtotal': float(item_subtotal)
                    }
                    supabase.table('order_items').insert(order_item_data).execute()
                    
                    # Update product total_sold
                    update_product_total_sold_supabase(item['product_id'], item['quantity'])
                    
                    # Update variant stock
                    if item.get('variant_id'):
                        update_product_stock_supabase(item['variant_id'], item['quantity'])
            
            # Remove items from cart
            for cart_id in cart_ids:
                supabase.table('cart').delete().eq('cart_id', cart_id).execute()
            
            # Mark voucher as used
            if buyer_voucher_id:
                use_voucher_supabase(buyer_voucher_id, buyer_id)
                print(f"Voucher {buyer_voucher_id} marked as used")
            
            return jsonify({'success': True, 'message': 'Order placed successfully', 'order_ids': order_ids})
        
        except Exception as e:
            print(f"Database error: {e}")
            import traceback
            print(traceback.format_exc())
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Unexpected error: {str(e)}'}), 500
