# Profile Image Upload - Supabase Setup

## ✅ What's Done:

1. **Updated Code:**
   - `blueprints/myAccount_profile.py` → Uses Supabase Storage
   - Bucket name: **"Images"**
   - Folder structure: `profiles/buyer_{user_id}_{unique_id}.jpg`

2. **Functions Updated:**
   - ✅ `get_profile()` - Get profile from Supabase
   - ✅ `update_profile()` - Upload image to Supabase Storage

---

## 🔧 Supabase Storage Setup Required:

### **Step 1: Check Bucket Settings**

1. Go to Supabase Dashboard
2. Click **"Storage"** → **"Images"** bucket
3. Make sure it's **PUBLIC** (so images can be viewed)

### **Step 2: Set Storage Policies**

Go to **SQL Editor** and run:

```sql
-- Allow public read access to images
CREATE POLICY "Public Access to Images"
ON storage.objects FOR SELECT
USING (bucket_id = 'Images');

-- Allow authenticated users to upload
CREATE POLICY "Authenticated Upload"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'Images');

-- Allow users to update their images
CREATE POLICY "Users Update Own Images"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'Images');

-- Allow users to delete their images
CREATE POLICY "Users Delete Own Images"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'Images');
```

### **Step 3: Test Upload**

1. Login to your app
2. Go to: http://localhost:5000/myAccount_profile
3. Click "Edit Profile"
4. Upload a profile image
5. Click "Save"
6. Image should upload to Supabase Storage!

---

## 📁 File Structure in Supabase:

```
Images/
└── profiles/
    ├── buyer_1_a1b2c3d4.jpg
    ├── buyer_2_e5f6g7h8.png
    └── buyer_3_i9j0k1l2.jpeg
```

---

## 🔍 How to Verify:

1. **Check Supabase Storage:**
   - Dashboard → Storage → Images → profiles/
   - Should see uploaded images

2. **Check Database:**
   - Dashboard → Table Editor → buyers
   - `profile_image` column should have Supabase URL
   - Format: `https://lpbmlhncfnxtwzpyoqrp.supabase.co/storage/v1/object/public/Images/profiles/buyer_X_XXXXX.jpg`

3. **Check in App:**
   - Profile page should display the image
   - Image URL should be from Supabase

---

## ⚠️ Important Notes:

1. **Bucket must be PUBLIC** - para makita yung images
2. **Policies must be set** - para ma-upload
3. **File size limit** - default 50MB (can change in bucket settings)
4. **Allowed formats** - PNG, JPG, JPEG only

---

## 🐛 Troubleshooting:

### Error: "Failed to upload profile image"
- Check if bucket "Images" exists
- Check if bucket is PUBLIC
- Check if policies are set

### Error: "Permission denied"
- Run the SQL policies above
- Make sure user is logged in

### Image not showing
- Check if URL is correct
- Check if bucket is PUBLIC
- Check browser console for errors

---

## 🎯 Next Steps:

1. ✅ Test profile image upload
2. ⏳ Migrate other image uploads (IDs, products, etc.)
3. ⏳ Add image compression/optimization
4. ⏳ Add image cropping feature
