from flask import Blueprint, jsonify, request, session
from database.db_config import get_supabase_client
from datetime import datetime, timedelta

chat_api_bp = Blueprint('chat_api', __name__)

@chat_api_bp.route('/api/chat/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for the logged-in user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    user_type = session.get('user_type', 'buyer')
    
    print(f"💬 Getting conversations for {user_type} user_id={user_id}")
    
    try:
        supabase = get_supabase_client()
        
        if user_type == 'buyer':
            # Get buyer_id
            buyer_response = supabase.table('buyers').select('buyer_id').eq('user_id', user_id).execute()
            if not buyer_response.data:
                return jsonify({'conversations': []}), 200
            buyer_id = buyer_response.data[0]['buyer_id']
            
            # Get all conversations for buyer
            conversations_response = supabase.table('conversations').select('*').eq('buyer_id', buyer_id).not_.is_('last_message', 'null').order('last_message_at', desc=True).execute()
            
            conversations = []
            for conv in conversations_response.data:
                # Determine contact type and get contact info
                if conv.get('rider_id'):
                    # Rider conversation
                    rider_response = supabase.table('riders').select('first_name, last_name, profile_image').eq('rider_id', conv['rider_id']).execute()
                    if rider_response.data:
                        rider = rider_response.data[0]
                        contact_name = f"{rider['first_name']} {rider['last_name']}"
                        contact_avatar = rider.get('profile_image')
                        contact_id = conv['rider_id']
                        contact_type = 'rider'
                    else:
                        continue
                else:
                    # Seller conversation
                    seller_response = supabase.table('sellers').select('shop_name, shop_logo').eq('seller_id', conv['seller_id']).execute()
                    if seller_response.data:
                        seller = seller_response.data[0]
                        contact_name = seller['shop_name']
                        contact_avatar = seller.get('shop_logo')
                        contact_id = conv['seller_id']
                        contact_type = 'seller'
                    else:
                        continue
                
                # For rider conversations, look at ALL deliveries between this
                # buyer and rider (not just the one stored on the conversation
                # row, which may be stale). If ANY delivery is still active
                # (in_transit, assigned, etc.) OR delivered-but-not-yet-confirmed
                # by the buyer, treat the chat as ongoing.
                delivery_status = None
                order_received = None

                if contact_type == 'rider':
                    has_active = False
                    has_unconfirmed = False
                    try:
                        # The deliveries table has rider_id but NOT buyer_id;
                        # the buyer link lives on the related order. Query the
                        # buyer's orders first, then check matching deliveries
                        # that belong to this rider.
                        orders_resp = supabase.table('orders').select(
                            'order_id, order_received, order_status'
                        ).eq('buyer_id', buyer_id).execute()

                        order_status_by_id = {}
                        for o in (orders_resp.data or []):
                            order_status_by_id[o['order_id']] = o

                        if order_status_by_id:
                            deliveries_resp = supabase.table('deliveries').select(
                                'status, order_id'
                            ).eq('rider_id', conv['rider_id']).in_(
                                'order_id', list(order_status_by_id.keys())
                            ).execute()

                            active_statuses = {'assigned', 'in_transit', 'pending'}
                            for d in (deliveries_resp.data or []):
                                d_status = d.get('status')
                                if d_status in active_statuses:
                                    has_active = True
                                related_order = order_status_by_id.get(d.get('order_id'))
                                if not related_order:
                                    continue
                                if related_order.get('order_status') == 'cancelled':
                                    continue
                                if not related_order.get('order_received'):
                                    has_unconfirmed = True
                    except Exception as lookup_err:
                        print(f"⚠️ rider chat status lookup failed: {lookup_err}")

                    # Frontend uses (delivery_status, order_received) to decide
                    # whether to keep the chat visible/unlocked.
                    if has_active or has_unconfirmed:
                        delivery_status = 'in_transit'
                        order_received = False
                    else:
                        delivery_status = 'delivered'
                        order_received = True
                else:
                    # Non-rider conversations don't gate visibility on delivery
                    if conv.get('delivery_id'):
                        delivery_response = supabase.table('deliveries').select(
                            'status'
                        ).eq('delivery_id', conv['delivery_id']).execute()
                        if delivery_response.data:
                            delivery_status = delivery_response.data[0].get('status')
                
                conversations.append({
                    'conversation_id': conv['conversation_id'],
                    'seller_id': conv.get('seller_id'),
                    'rider_id': conv.get('rider_id'),
                    'delivery_id': conv.get('delivery_id'),
                    'delivery_status': delivery_status,
                    'order_received': order_received,
                    'contact_id': contact_id,
                    'contact_name': contact_name,
                    'contact_avatar': contact_avatar,
                    'contact_type': contact_type,
                    'last_message': conv['last_message'],
                    'last_message_time': conv['last_message_at'],
                    'unread_count': conv.get('buyer_unread_count', 0)
                })
            
            print(f"✅ Loaded {len(conversations)} conversations for buyer")
            
        elif user_type == 'seller':
            # Get seller_id
            seller_response = supabase.table('sellers').select('seller_id').eq('user_id', user_id).execute()
            if not seller_response.data:
                return jsonify({'conversations': []}), 200
            seller_id = seller_response.data[0]['seller_id']
            
            # Get buyer conversations for seller
            conversations_response = supabase.table('conversations').select('*').eq('seller_id', seller_id).order('last_message_at', desc=True).execute()
            
            conversations = []
            for conv in conversations_response.data:
                # Get buyer info
                buyer_response = supabase.table('buyers').select('first_name, last_name, profile_image').eq('buyer_id', conv['buyer_id']).execute()
                if buyer_response.data:
                    buyer = buyer_response.data[0]
                    print(f"👤 Buyer: {buyer['first_name']} {buyer['last_name']}, Avatar: {buyer.get('profile_image')}")
                    conversations.append({
                        'conversation_id': conv['conversation_id'],
                        'contact_id': conv['buyer_id'],
                        'contact_name': f"{buyer['first_name']} {buyer['last_name']}",
                        'contact_avatar': buyer.get('profile_image'),
                        'last_message': conv['last_message'],
                        'last_message_time': conv['last_message_at'],
                        'unread_count': conv.get('seller_unread_count', 0),
                        'contact_type': 'buyer'
                    })
            
            print(f"✅ Loaded {len(conversations)} conversations for seller")
            print(f"📋 Conversations data: {conversations}")
        else:
            conversations = []
        
        return jsonify({'conversations': conversations}), 200
        
    except Exception as e:
        print(f"❌ Error getting conversations: {e}")
        return jsonify({'error': str(e)}), 500

@chat_api_bp.route('/api/chat/messages/<int:conversation_id>', methods=['GET'])
def get_messages(conversation_id):
    """Get all messages for a specific conversation"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    user_type = session.get('user_type', 'buyer')
    
    print(f"💬 Getting messages for conversation_id={conversation_id}")
    
    try:
        supabase = get_supabase_client()
        
        # Get chat messages
        messages_response = supabase.table('messages').select('*').eq('conversation_id', conversation_id).order('created_at').execute()
        
        messages = messages_response.data
        
        # Mark messages as read based on user type
        if user_type == 'buyer':
            # Mark seller messages as read
            supabase.table('messages').update({'is_read': True}).eq('conversation_id', conversation_id).eq('sender_type', 'seller').eq('is_read', False).execute()
            
            # Reset buyer unread count
            supabase.table('conversations').update({'buyer_unread_count': 0}).eq('conversation_id', conversation_id).execute()
            
        elif user_type == 'seller':
            # Mark buyer messages as read
            supabase.table('messages').update({'is_read': True}).eq('conversation_id', conversation_id).eq('sender_type', 'buyer').eq('is_read', False).execute()
            
            # Reset seller unread count
            supabase.table('conversations').update({'seller_unread_count': 0}).eq('conversation_id', conversation_id).execute()
        
        print(f"✅ Loaded {len(messages)} messages")
        
        return jsonify({'messages': messages}), 200
        
    except Exception as e:
        print(f"❌ Error getting messages: {e}")
        return jsonify({'error': str(e)}), 500

@chat_api_bp.route('/api/chat/send', methods=['POST'])
def send_message():
    """Send a new message"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    contact_id = data.get('contact_id')
    message_text = data.get('message_text', '').strip()
    
    if not message_text:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    user_id = session['user_id']
    user_type = session.get('user_type', 'buyer')
    
    print(f"💬 Sending message from {user_type}")
    
    try:
        supabase = get_supabase_client()
        
        # Handle buyer-seller chat messages
        if user_type == 'buyer':
            buyer_response = supabase.table('buyers').select('buyer_id').eq('user_id', user_id).execute()
            if not buyer_response.data:
                return jsonify({'error': 'Buyer profile not found'}), 404
            sender_id = buyer_response.data[0]['buyer_id']
            
            # Get current timestamp with +8 hours for Philippine time
            current_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            
            if not conversation_id:
                # Create new conversation
                conv_data = {
                    'buyer_id': sender_id,
                    'seller_id': contact_id,
                    'last_message': message_text,
                    'last_message_at': current_time
                }
                conv_response = supabase.table('conversations').insert(conv_data).execute()
                conversation_id = conv_response.data[0]['conversation_id']
            else:
                # Update existing conversation
                supabase.table('conversations').update({
                    'last_message': message_text,
                    'last_message_at': current_time,
                    'seller_unread_count': supabase.table('conversations').select('seller_unread_count').eq('conversation_id', conversation_id).execute().data[0]['seller_unread_count'] + 1
                }).eq('conversation_id', conversation_id).execute()
            
            # Insert message
            msg_data = {
                'conversation_id': conversation_id,
                'sender_type': 'buyer',
                'sender_id': sender_id,
                'message_text': message_text,
                'created_at': current_time
            }
            msg_response = supabase.table('messages').insert(msg_data).execute()
            message = msg_response.data[0]
            
        elif user_type == 'seller':
            seller_response = supabase.table('sellers').select('seller_id').eq('user_id', user_id).execute()
            if not seller_response.data:
                return jsonify({'error': 'Seller profile not found'}), 404
            sender_id = seller_response.data[0]['seller_id']
            
            # Get current timestamp with +8 hours for Philippine time
            current_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            
            if not conversation_id:
                # Create new conversation
                conv_data = {
                    'buyer_id': contact_id,
                    'seller_id': sender_id,
                    'last_message': message_text,
                    'last_message_at': current_time
                }
                conv_response = supabase.table('conversations').insert(conv_data).execute()
                conversation_id = conv_response.data[0]['conversation_id']
            else:
                # Update existing conversation
                supabase.table('conversations').update({
                    'last_message': message_text,
                    'last_message_at': current_time,
                    'buyer_unread_count': supabase.table('conversations').select('buyer_unread_count').eq('conversation_id', conversation_id).execute().data[0]['buyer_unread_count'] + 1
                }).eq('conversation_id', conversation_id).execute()
            
            # Insert message
            msg_data = {
                'conversation_id': conversation_id,
                'sender_type': 'seller',
                'sender_id': sender_id,
                'message_text': message_text,
                'created_at': current_time
            }
            msg_response = supabase.table('messages').insert(msg_data).execute()
            message = msg_response.data[0]
        
        print(f"✅ Message sent successfully")
        
        return jsonify({
            'success': True,
            'message': message,
            'conversation_id': conversation_id
        }), 200
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return jsonify({'error': str(e)}), 500

@chat_api_bp.route('/api/chat/search-sellers', methods=['GET'])
def search_sellers():
    """Search all sellers by shop name"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'sellers': []}), 200
    
    print(f"🔍 Searching sellers: {query}")
    
    try:
        supabase = get_supabase_client()
        
        # Search sellers by shop name
        sellers_response = supabase.table('sellers').select('seller_id, shop_name, shop_logo, shop_description').ilike('shop_name', f'%{query}%').order('shop_name').limit(20).execute()
        
        sellers = sellers_response.data
        
        print(f"✅ Found {len(sellers)} sellers")
        
        return jsonify({'sellers': sellers}), 200
        
    except Exception as e:
        print(f"❌ Error searching sellers: {e}")
        return jsonify({'error': str(e)}), 500

@chat_api_bp.route('/api/chat/start-conversation', methods=['POST'])
def start_conversation():
    """Start a new conversation with a seller"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    seller_id = data.get('seller_id')
    
    if not seller_id:
        return jsonify({'error': 'Seller ID required'}), 400
    
    user_id = session['user_id']
    
    print(f"💬 Starting conversation with seller_id={seller_id}")
    
    try:
        supabase = get_supabase_client()
        
        # Get buyer_id
        buyer_response = supabase.table('buyers').select('buyer_id').eq('user_id', user_id).execute()
        if not buyer_response.data:
            return jsonify({'error': 'Buyer profile not found'}), 404
        buyer_id = buyer_response.data[0]['buyer_id']
        
        # Check if conversation already exists
        existing_response = supabase.table('conversations').select('conversation_id').eq('buyer_id', buyer_id).eq('seller_id', seller_id).execute()
        
        if existing_response.data:
            conversation_id = existing_response.data[0]['conversation_id']
            print(f"✅ Using existing conversation_id={conversation_id}")
        else:
            # Create new conversation with +8 hours for Philippine time
            current_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            conv_data = {
                'buyer_id': buyer_id,
                'seller_id': seller_id,
                'last_message': '',
                'last_message_at': current_time
            }
            conv_response = supabase.table('conversations').insert(conv_data).execute()
            conversation_id = conv_response.data[0]['conversation_id']
            print(f"✅ Created new conversation_id={conversation_id}")
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id
        }), 200
        
    except Exception as e:
        print(f"❌ Error starting conversation: {e}")
        return jsonify({'error': str(e)}), 500
