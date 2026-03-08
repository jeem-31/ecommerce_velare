from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database.supabase_helper import *
from werkzeug.utils import secure_filename
import os
from datetime import datetime

rider_report_user_bp = Blueprint('rider_report_user', __name__)

UPLOAD_FOLDER = 'static/uploads/reports'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@rider_report_user_bp.route('/rider/reports', methods=['GET'])
def report_user_page():
    """Display report user form and my reports"""
    if 'user_id' not in session or session.get('user_type') != 'rider':
        flash('Please login as rider', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        print("=" * 60)
        print("🔍 RIDER REPORT USER PAGE - Loading")
        print("=" * 60)
        
        # Get rider info
        rider = get_rider_by_user_id(session['user_id'])
        
        if not rider:
            flash('Rider not found', 'error')
            return redirect(url_for('auth.login'))
        
        print(f"👤 Rider: {rider.get('first_name')} {rider.get('last_name')}")
        
        # Get recent deliveries with buyers and sellers
        deliveries_data = get_rider_deliveries_with_users(rider['rider_id'])
        print(f"📦 Loaded {len(deliveries_data)} deliveries with user info")
        
        # Format deliveries
        deliveries = []
        for delivery in deliveries_data:
            order = delivery.get('orders', {})
            buyer = order.get('buyers', {})
            seller = order.get('sellers', {})
            
            deliveries.append({
                'delivery_id': delivery['delivery_id'],
                'order_id': order.get('order_id'),
                'order_number': order.get('order_number'),
                'buyer_id': order.get('buyer_id'),
                'buyer_name': f"{buyer.get('first_name', '')} {buyer.get('last_name', '')}",
                'seller_id': order.get('seller_id'),
                'seller_name': seller.get('shop_name')
            })
        
        # Get rider's reports
        reports = get_rider_reports(session['user_id'])
        print(f"📋 Loaded {len(reports)} reports")
        
        print("✅ Page loaded successfully")
        print("=" * 60)
        
        return render_template('rider/rider_reports.html', 
                             rider=rider, 
                             deliveries=deliveries,
                             reports=reports)
    except Exception as e:
        print(f"❌ Error loading reports page: {e}")
        flash('Failed to load reports page', 'error')
        return redirect(url_for('rider_dashboard.rider_dashboard'))

@rider_report_user_bp.route('/rider/submit-report', methods=['POST'])
def submit_report():
    """Submit a report"""
    if 'user_id' not in session or session.get('user_type') != 'rider':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        print("=" * 60)
        print("📝 SUBMIT REPORT - Processing")
        print("=" * 60)
        
        reported_type = request.form.get('reported_type')
        reported_id = request.form.get('reported_id')
        category = request.form.get('category')
        reason = request.form.get('reason')
        
        print(f"🔍 Reporting {reported_type} ID: {reported_id}")
        print(f"📋 Category: {category}")
        
        # Get order_id and delivery_id, convert 'None' string to actual None
        order_id_raw = request.form.get('order_id', '')
        if order_id_raw and order_id_raw != 'None' and order_id_raw != 'null':
            try:
                order_id = int(order_id_raw)
                print(f"✅ Order ID: {order_id}")
            except (ValueError, TypeError):
                order_id = None
                print(f"⚠️ Invalid order_id, setting to None")
        else:
            order_id = None
        
        delivery_id_raw = request.form.get('delivery_id', '')
        if delivery_id_raw and delivery_id_raw != 'None' and delivery_id_raw != 'null':
            try:
                delivery_id = int(delivery_id_raw)
                print(f"✅ Delivery ID: {delivery_id}")
            except (ValueError, TypeError):
                delivery_id = None
                print(f"⚠️ Invalid delivery_id, setting to None")
        else:
            delivery_id = None
        
        supabase = get_supabase()
        
        # Get reported user_id
        if reported_type == 'buyer':
            user_response = supabase.table('buyers').select('user_id').eq('buyer_id', reported_id).execute()
        elif reported_type == 'seller':
            user_response = supabase.table('sellers').select('user_id').eq('seller_id', reported_id).execute()
        else:
            print(f"❌ Invalid user type: {reported_type}")
            return jsonify({'success': False, 'message': 'Invalid user type'}), 400
        
        if not user_response.data:
            print(f"❌ User not found")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        reported_user_id = user_response.data[0]['user_id']
        print(f"👤 Reported user_id: {reported_user_id}")
        
        # Handle file upload
        evidence_path = None
        if 'evidence' in request.files:
            file = request.files['evidence']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                evidence_path = file_path.replace('\\', '/')
                print(f"📸 Evidence uploaded: {filename}")
        
        # Insert report using helper function
        report_data = {
            'reporter_id': session['user_id'],
            'reporter_type': 'rider',
            'reported_user_id': reported_user_id,
            'reported_user_type': reported_type,
            'report_category': category,
            'report_reason': reason,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        # Add optional fields only if they have values
        if order_id:
            report_data['order_id'] = order_id
        if delivery_id:
            report_data['delivery_id'] = delivery_id
        if evidence_path:
            report_data['evidence_image'] = evidence_path
        
        report = insert_user_report(report_data)
        
        if not report:
            print(f"❌ Failed to insert report")
            return jsonify({'success': False, 'message': 'Failed to submit report'}), 500
        
        print(f"✅ Report created: {report.get('report_id')}")
        
        # Update report count
        report_count = get_user_report_count(reported_user_id)
        print(f"📊 Report count for user: {report_count}")
        
        if reported_type == 'buyer':
            # Get buyer_id from user_id
            buyer_response = supabase.table('buyers').select('buyer_id').eq('user_id', reported_user_id).execute()
            if buyer_response.data:
                buyer_id = buyer_response.data[0]['buyer_id']
                supabase.table('buyers').update({'report_count': report_count}).eq('buyer_id', buyer_id).execute()
                print(f"✅ Updated buyer report count")
        elif reported_type == 'seller':
            # Get seller_id from user_id
            seller_response = supabase.table('sellers').select('seller_id').eq('user_id', reported_user_id).execute()
            if seller_response.data:
                seller_id = seller_response.data[0]['seller_id']
                update_seller_report_count(seller_id, report_count)
                print(f"✅ Updated seller report count")
        
        # Send notification to the reported user
        try:
            from blueprints.notification_helper import create_report_notification
            create_report_notification(reported_user_id, reported_type, category)
            print(f"📤 Notification sent")
        except Exception as notif_error:
            print(f"⚠️ Failed to send notification: {notif_error}")
        
        print("✅ Report submitted successfully")
        print("=" * 60)
        
        return jsonify({'success': True, 'message': 'Report submitted successfully'})
    
    except Exception as e:
        print(f"❌ Error submitting report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


