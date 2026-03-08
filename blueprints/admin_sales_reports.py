from flask import Blueprint, render_template, make_response, request
from database.db_config import get_supabase_client
import csv
from io import StringIO, BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

admin_sales_reports_bp = Blueprint('admin_sales_reports', __name__)

@admin_sales_reports_bp.route('/admin/sales-reports')
def admin_sales_reports():
    print("📊 Loading admin sales reports...")
    supabase = get_supabase_client()
    
    try:
        # Get total sales from delivered orders
        orders_response = supabase.table('orders').select('order_id, total_amount, commission_amount, seller_id').eq('order_status', 'delivered').execute()
        total_sales = sum(order['total_amount'] for order in orders_response.data if order.get('total_amount'))
        
        # Get total delivered orders
        total_orders = len(orders_response.data)
        
        # Get total commission from delivered orders
        total_commission = sum(order['commission_amount'] for order in orders_response.data if order.get('commission_amount'))
        
        # Get sales by category - Show ALL predefined categories even with 0 sales
        predefined_categories = [
            'Dresses', 'Skirts', 'Tops', 'Blouses', 'Activewear',
            'Yoga Pants', 'Lingerie', 'Sleepwear', 'Jackets', 'Coats',
            'Shoes', 'Accessories'
        ]
        
        # Fetch all order items with product info for delivered orders
        order_items_response = supabase.table('order_items').select('order_id, product_id, subtotal, quantity').execute()
        products_response = supabase.table('products').select('product_id, category').execute()
        
        # Create product category map
        product_categories = {p['product_id']: p['category'] for p in products_response.data}
        
        # Get delivered order IDs
        delivered_order_ids = [order['order_id'] for order in orders_response.data]
        
        # Group by category
        category_stats = {cat: {'total_sales': 0.0, 'order_count': 0, 'items_sold': 0} for cat in predefined_categories}
        order_categories = {}  # Track which orders have which categories
        
        for item in order_items_response.data:
            if item['order_id'] in delivered_order_ids:
                category = product_categories.get(item['product_id'])
                if category in category_stats:
                    category_stats[category]['total_sales'] += float(item['subtotal']) if item.get('subtotal') else 0
                    category_stats[category]['items_sold'] += item['quantity']
                    
                    # Track unique orders per category
                    if category not in order_categories:
                        order_categories[category] = set()
                    order_categories[category].add(item['order_id'])
        
        # Update order counts
        for cat in category_stats:
            if cat in order_categories:
                category_stats[cat]['order_count'] = len(order_categories[cat])
        
        # Format category data
        formatted_categories = []
        for cat in predefined_categories:
            stats = category_stats[cat]
            formatted_categories.append({
                'category': cat,
                'total_sales': stats['total_sales'],
                'order_count': stats['order_count'],
                'items_sold': stats['items_sold'],
                'percentage': (stats['total_sales'] / total_sales * 100) if total_sales > 0 else 0
            })
        
        # Sort by total_sales descending
        formatted_categories.sort(key=lambda x: x['total_sales'], reverse=True)
        
        # Get top sellers by sales
        sellers_response = supabase.table('sellers').select('seller_id, shop_name, first_name, last_name').execute()
        sellers_map = {s['seller_id']: s for s in sellers_response.data}
        
        # Group orders by seller
        seller_stats = {}
        for order in orders_response.data:
            seller_id = order['seller_id']
            if seller_id not in seller_stats:
                seller_stats[seller_id] = {'total_sales': 0.0, 'order_count': 0, 'orders': []}
            seller_stats[seller_id]['total_sales'] += float(order['total_amount'])
            seller_stats[seller_id]['order_count'] += 1
            seller_stats[seller_id]['orders'].append(float(order['total_amount']))
        
        # Format seller data
        formatted_sellers = []
        for seller_id, stats in seller_stats.items():
            if seller_id in sellers_map:
                seller = sellers_map[seller_id]
                formatted_sellers.append({
                    'seller_id': seller_id,
                    'store_name': seller['shop_name'],
                    'name': f"{seller['first_name']} {seller['last_name']}",
                    'total_sales': stats['total_sales'],
                    'order_count': stats['order_count'],
                    'avg_order_value': stats['total_sales'] / stats['order_count'] if stats['order_count'] > 0 else 0
                })
        
        # Sort by total_sales and limit to top 10
        formatted_sellers.sort(key=lambda x: x['total_sales'], reverse=True)
        formatted_sellers = formatted_sellers[:10]
        
        # Get sales trend (last 7 days)
        from datetime import timedelta
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        trend_response = supabase.table('orders').select('created_at, total_amount, order_id').eq('order_status', 'delivered').gte('created_at', seven_days_ago).execute()
        
        # Group by date
        from collections import defaultdict
        daily_stats = defaultdict(lambda: {'sales': 0.0, 'orders': 0})
        
        for order in trend_response.data:
            created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            date_key = created_at.strftime('%Y-%m-%d')
            daily_stats[date_key]['sales'] += float(order['total_amount'])
            daily_stats[date_key]['orders'] += 1
        
        # Format trend data
        formatted_trend = []
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            date_obj = datetime.strptime(date_key, '%Y-%m-%d')
            formatted_trend.append({
                'date': date_obj.strftime('%b %d'),
                'sales': stats['sales'],
                'orders': stats['orders']
            })
        
        # Get detailed sales breakdown (last 20 delivered orders)
        detailed_orders = supabase.table('orders').select('order_id, order_number, total_amount, commission_amount, created_at, buyer_id, seller_id').eq('order_status', 'delivered').order('created_at', desc=True).limit(20).execute()
        
        # Fetch buyers and sellers for these orders
        buyer_ids = list(set(order['buyer_id'] for order in detailed_orders.data))
        seller_ids = list(set(order['seller_id'] for order in detailed_orders.data))
        
        buyers_response = supabase.table('buyers').select('buyer_id, first_name, last_name').in_('buyer_id', buyer_ids).execute()
        sellers_response = supabase.table('sellers').select('seller_id, shop_name').in_('seller_id', seller_ids).execute()
        
        buyers_map = {b['buyer_id']: b for b in buyers_response.data}
        sellers_map = {s['seller_id']: s for s in sellers_response.data}
        
        # Get order items for these orders
        order_ids = [order['order_id'] for order in detailed_orders.data]
        items_response = supabase.table('order_items').select('order_id, product_id').in_('order_id', order_ids).execute()
        
        # Group items by order
        order_items_map = defaultdict(list)
        for item in items_response.data:
            order_items_map[item['order_id']].append(item['product_id'])
        
        # Format detailed sales data
        formatted_detailed = []
        for order in detailed_orders.data:
            buyer = buyers_map.get(order['buyer_id'], {})
            seller = sellers_map.get(order['seller_id'], {})
            product_ids = order_items_map.get(order['order_id'], [])
            
            # Get categories for products
            categories = set()
            for pid in product_ids:
                if pid in product_categories:
                    categories.add(product_categories[pid])
            
            created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            
            formatted_detailed.append({
                'order_id': order['order_id'],
                'order_number': order['order_number'],
                'amount': float(order['total_amount']),
                'commission': float(order['commission_amount']),
                'date': created_at.strftime('%b %d, %Y'),
                'buyer': f"{buyer.get('first_name', 'Unknown')} {buyer.get('last_name', '')}".strip(),
                'seller': seller.get('shop_name', 'Unknown'),
                'item_count': len(product_ids),
                'categories': ', '.join(categories) if categories else 'N/A'
            })
        
        stats = {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'total_commission': total_commission,
            'sales_by_category': formatted_categories,
            'top_sellers': formatted_sellers,
            'sales_trend': formatted_trend,
            'detailed_sales': formatted_detailed
        }
        
        print(f"✅ Sales reports loaded successfully")
        
    except Exception as e:
        print(f"❌ Error fetching sales reports: {e}")
        stats = {
            'total_sales': 0.0,
            'total_orders': 0,
            'total_commission': 0.0,
            'sales_by_category': [],
            'top_sellers': [],
            'sales_trend': [],
            'detailed_sales': []
        }
    
    return render_template('admin/admin_sales_reports.html', stats=stats)



@admin_sales_reports_bp.route('/admin/sales-reports/export-csv')
def export_csv():
    """Export sales reports to CSV format"""
    print("📄 Exporting sales report to CSV...")
    supabase = get_supabase_client()
    
    try:
        # Get filter parameters
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        category = request.args.get('category', '')
        
        # Build query
        query = supabase.table('orders').select('order_id, order_number, created_at, total_amount, commission_amount, shipping_fee, buyer_id, seller_id').eq('order_status', 'delivered')
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').isoformat()
            query = query.gte('created_at', start_dt)
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59).isoformat()
            query = query.lte('created_at', end_dt)
        
        sales_data = query.order('created_at', desc=True).execute().data
        
        # If category filter, filter by products
        if category:
            # Get products in this category
            products_response = supabase.table('products').select('product_id').eq('category', category).execute()
            product_ids = [p['product_id'] for p in products_response.data]
            
            # Get order_ids that have these products
            items_response = supabase.table('order_items').select('order_id').in_('product_id', product_ids).execute()
            filtered_order_ids = set(item['order_id'] for item in items_response.data)
            
            # Filter sales_data
            sales_data = [order for order in sales_data if order['order_id'] in filtered_order_ids]
        
        # Fetch related data
        if sales_data:
            buyer_ids = list(set(order['buyer_id'] for order in sales_data))
            seller_ids = list(set(order['seller_id'] for order in sales_data))
            order_ids = [order['order_id'] for order in sales_data]
            
            buyers_response = supabase.table('buyers').select('buyer_id, first_name, last_name').in_('buyer_id', buyer_ids).execute()
            sellers_response = supabase.table('sellers').select('seller_id, shop_name').in_('seller_id', seller_ids).execute()
            items_response = supabase.table('order_items').select('order_id, product_id, quantity').in_('order_id', order_ids).execute()
            
            # Get all product info
            product_ids = list(set(item['product_id'] for item in items_response.data))
            products_response = supabase.table('products').select('product_id, product_name, category').in_('product_id', product_ids).execute()
            
            buyers_map = {b['buyer_id']: b for b in buyers_response.data}
            sellers_map = {s['seller_id']: s for s in sellers_response.data}
            products_map = {p['product_id']: p for p in products_response.data}
            
            # Group items by order
            from collections import defaultdict
            order_items_map = defaultdict(list)
            for item in items_response.data:
                order_items_map[item['order_id']].append(item)
        else:
            buyers_map = {}
            sellers_map = {}
            products_map = {}
            order_items_map = {}
        
        # Get summary statistics
        total_orders = len(sales_data)
        total_sales = sum(float(order['total_amount']) for order in sales_data)
        total_commission = sum(float(order['commission_amount']) for order in sales_data)
        avg_order = total_sales / total_orders if total_orders > 0 else 0
        
        # Create CSV with proper business formatting
        output = StringIO()
        writer = csv.writer(output)
        
        # REPORT HEADER SECTION
        writer.writerow(['VELÁRE E-COMMERCE PLATFORM'])
        writer.writerow(['SALES REPORT'])
        writer.writerow([])
        writer.writerow(['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')])
        
        if start_date or end_date:
            date_range = f"{start_date or 'Beginning'} to {end_date or 'Present'}"
            writer.writerow(['Report Period:', date_range])
        else:
            writer.writerow(['Report Period:', 'All Time'])
            
        if category:
            writer.writerow(['Category Filter:', category])
        
        writer.writerow([])
        writer.writerow(['=' * 80])
        writer.writerow([])
        
        # EXECUTIVE SUMMARY SECTION
        writer.writerow(['EXECUTIVE SUMMARY'])
        writer.writerow([])
        
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Delivered Orders', f"{total_orders:,}"])
        writer.writerow(['Gross Sales Revenue', f"₱{total_sales:,.2f}"])
        writer.writerow(['Platform Commission Earned', f"₱{total_commission:,.2f}"])
        writer.writerow(['Average Order Value', f"₱{avg_order:,.2f}"])
        
        if total_sales > 0:
            commission_rate = (total_commission / total_sales) * 100
            writer.writerow(['Commission Rate', f"{commission_rate:.1f}%"])
        
        writer.writerow([])
        writer.writerow(['=' * 80])
        writer.writerow([])
        
        # DETAILED TRANSACTION RECORDS
        writer.writerow(['DETAILED TRANSACTION RECORDS'])
        writer.writerow([])
        writer.writerow([
            'Order No.',
            'Transaction Date',
            'Transaction Time',
            'Seller Name',
            'Buyer Name',
            'Items',
            'Subtotal',
            'Shipping',
            'Total Amount',
            'Commission (5%)',
            'Net to Seller',
            'Category',
            'Products Ordered'
        ])
        
        # Write data rows with calculations
        for row in sales_data:
            # Format datetime
            created_at = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
            date_str = created_at.strftime('%Y-%m-%d')
            time_str = created_at.strftime('%I:%M %p')
            
            # Get buyer and seller info
            buyer = buyers_map.get(row['buyer_id'], {})
            seller = sellers_map.get(row['seller_id'], {})
            buyer_name = f"{buyer.get('first_name', 'Unknown')} {buyer.get('last_name', '')}".strip()
            seller_name = seller.get('shop_name', 'Unknown')
            
            # Get items
            items = order_items_map.get(row['order_id'], [])
            total_items = len(items)
            
            # Get categories and products
            categories = set()
            products = []
            for item in items:
                product = products_map.get(item['product_id'], {})
                if product.get('category'):
                    categories.add(product['category'])
                if product.get('product_name'):
                    products.append(f"{product['product_name']} ({item['quantity']}x)")
            
            # Calculate values
            total_amount = float(row['total_amount'])
            commission = float(row['commission_amount'])
            shipping = float(row['shipping_fee']) if row.get('shipping_fee') else 0.0
            subtotal = total_amount - shipping
            net_to_seller = total_amount - commission
            
            writer.writerow([
                row['order_number'],
                date_str,
                time_str,
                seller_name,
                buyer_name,
                total_items,
                f"₱{subtotal:,.2f}",
                f"₱{shipping:,.2f}",
                f"₱{total_amount:,.2f}",
                f"₱{commission:,.2f}",
                f"₱{net_to_seller:,.2f}",
                ', '.join(categories).title() if categories else 'N/A',
                '; '.join(products) if products else 'N/A'
            ])
        
        # FOOTER SECTION
        writer.writerow([])
        writer.writerow(['=' * 80])
        writer.writerow([])
        writer.writerow(['END OF REPORT'])
        writer.writerow(['Total Records:', len(sales_data)])
        writer.writerow([])
        writer.writerow(['Note: All amounts are in Philippine Peso (₱)'])
        writer.writerow(['Commission rate: 5% of total order amount'])
        writer.writerow(['This is a system-generated report and does not require signature'])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=sales_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        print(f"✅ CSV export completed")
        return response
        
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        return f"Error exporting CSV: {str(e)}", 500
