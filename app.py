import streamlit as st
import sqlite3
import datetime
import base64

# 1. إعداد قاعدة البيانات
def init_db():
    with sqlite3.connect("complaints.db") as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                national_id TEXT,
                details TEXT,
                department TEXT,
                location TEXT,
                images TEXT,
                status TEXT,
                created_at TEXT,
                responses TEXT
            )
        ''')
        conn.commit()

init_db()

# 2. حسابات المشرفين والإدارة
ADMIN_USERS = {
    "admin1": {"password": "admin", "name": "المشرف سلطان"},
    "manager1": {"password": "mgr", "name": "المدير"}
}

st.set_page_config(page_title="متطلبات وشكاوى متدربين المعهد الصناعي", page_icon="📋", layout="centered")

# إدارة حالة الجلسة
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "admin_name" not in st.session_state:
    st.session_state["admin_name"] = ""

# --- 1. زر تسجيل الدخول في الأعلى كمربع منسدل ---
if not st.session_state["is_admin"]:
    with st.expander("🔐 تسجيل دخول الإداريين"):
        admin_user = st.text_input("اسم المستخدم", key="admin_u")
        admin_pass = st.text_input("كلمة المرور", type="password", key="admin_p")
        if st.button("دخول الإدارة", use_container_width=True):
            if admin_user in ADMIN_USERS and ADMIN_USERS[admin_user]["password"] == admin_pass:
                st.session_state["is_admin"] = True
                st.session_state["admin_name"] = ADMIN_USERS[admin_user]["name"]
                st.success("تم تسجيل الدخول بنجاح")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة")
else:
    st.success(f"مرحباً: {st.session_state['admin_name']}")
    if st.button("تسجيل الخروج", use_container_width=True):
        st.session_state["is_admin"] = False
        st.session_state["admin_name"] = ""
        st.rerun()

# --- 2. الواجهة الرئيسية (نموذج تقديم الشكوى) ---
if not st.session_state["is_admin"]:
    st.markdown("<h2 style='text-align: center;'>متطلبات وشكاوى متدربين المعهد الصناعي</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("<h3 style='text-align: center;'>📝 نموذج تقديم شكوى أو متطلب جديد</h3>", unsafe_allow_html=True)
    st.caption("الرجاء تعبئة الحقول أدناه بدقة:")
    
    with st.form("complaint_form", clear_on_submit=True):
        details = st.text_area("1. اكتب المشكلة أو الطلب بالتفصيل:", placeholder="...اكتب تفاصيل الطلب هنا")
        department = st.selectbox("2. القسم:", ["قسم الحاسب الآلي", "قسم الكهرباء", "قسم الميكانيكا", "خدمات ومتطلبات أخرى"])
        location = st.text_input("3. مكان المشكلة (مثال: القاعة الفلانية، المعمل رقم...):")
        national_id = st.text_input("رقم الهوية / الإقامة:")
        
        uploaded_files = st.file_uploader("4. إرفاق صور للمشكلة (يمكنك اختيار حتى 5 صور):", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        
        submitted = st.form_submit_button("إرسال الطلب", use_container_width=True)
        
        if submitted:
            if national_id and details and location:
                if uploaded_files and len(uploaded_files) > 5:
                    st.error("عذراً، حد المرفقات الأقصى هو 5 صور فقط.")
                else:
                    encoded_images = []
                    if uploaded_files:
                        for file in uploaded_files[:5]:
                            b64 = base64.b64encode(file.read()).decode('utf-8')
                            encoded_images.append(b64)
                    
                    images_str = "|||".join(encoded_images)

                    with sqlite3.connect("complaints.db") as conn:
                        c = conn.cursor()
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute(
                            "INSERT INTO complaints (national_id, details, department, location, images, status, created_at, responses) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (national_id, details, department, location, images_str, "جديد", now, "")
                        )
                        conn.commit()
                    st.success("تم إرسال بلاغك بنجاح!")
                    st.rerun()
            else:
                st.warning("يرجى تعبئة كافة الحقول المطلوبة ورقم الهوية.")

    st.markdown("---")
    st.subheader("🔍 الاستعلام عن طلب سابق")
    search_nid = st.text_input("أدخل رقم الهوية لمتابعة طلباتك:")
    
    if search_nid:
        with sqlite3.connect("complaints.db") as conn:
            c = conn.cursor()
            c.execute("SELECT id, details, department, location, status, created_at, responses, images FROM complaints WHERE national_id = ?", (search_nid,))
            my_requests = c.fetchall()

        if not my_requests:
            st.info("لا توجد بلاغات مرتبطة برقم الهوية هذا.")
        else:
            for req in my_requests:
                with st.expander(f"طلب #{req[0]} - القسم: {req[2]} ({req[4]})"):
                    st.write(f"**المكان:** {req[3]}")
                    st.write(f"**التفاصيل:** {req[1]}")
                    st.write(f"**التاريخ:** {req[5]}")
                    
                    if req[7]:
                        imgs = [i for i in req[7].split("|||") if i]
                        if imgs:
                            st.write(f"**الصور المرفقة ({len(imgs)}):**")
                            cols = st.columns(min(len(imgs), 5))
                            for idx, img_b64 in enumerate(imgs):
                                cols[idx].image(base64.b64decode(img_b64), caption=f"صورة {idx+1}", use_container_width=True)

                    if req[6]:
                        st.write(f"**ردود الإدارة:**\n{req[6]}")

# --- 3. واجهة الإدارة والمشرفين (تظهر بعد الدخول) ---
else:
    st.subheader("📊 لوحة إدارة الشكاوى والطلبات")
    
    with sqlite3.connect("complaints.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM complaints ORDER BY id DESC")
        all_requests = c.fetchall()

    if not all_requests:
        st.info("لا توجد طلبات مسجلة حالياً.")
    else:
        for req in all_requests:
            req_id, nid, r_det, r_dept, r_loc, r_imgs, r_status, r_time, r_resp = req
            
            with st.expander(f"طلب #{req_id}: قسم {r_dept} - الحالة: [{r_status}]"):
                st.write(f"**رقم الهوية:** {nid} | **المكان:** {r_loc} | **التاريخ:** {r_time}")
                st.write(f"**التفاصيل:** {r_det}")
                
                if r_imgs:
                    imgs = [i for i in r_imgs.split("|||") if i]
                    if imgs:
                        st.write(f"**الصور المرفقة ({len(imgs)}):**")
                        cols = st.columns(min(len(imgs), 5))
                        for idx, img_b64 in enumerate(imgs):
                            cols[idx].image(base64.b64decode(img_b64), caption=f"صورة {idx+1}", use_container_width=True)

                st.markdown("---")
                
                status_options = ["جديد", "قيد المعالجة", "مغلق"]
                status_index = status_options.index(r_status) if r_status in status_options else 0
                
                new_status = st.selectbox("تحديث الحالة", status_options, index=status_index, key=f"status_{req_id}")
                reply = st.text_input("إضافة رد", key=f"reply_{req_id}")
                
                if st.button("حفظ التحديث", key=f"save_{req_id}"):
                    with sqlite3.connect("complaints.db") as conn:
                        c = conn.cursor()
                        updated_resp = (r_resp + f"\n[{st.session_state['admin_name']}]: {reply}") if reply else r_resp
                        c.execute("UPDATE complaints SET status = ?, responses = ? WHERE id = ?", (new_status, updated_resp, req_id))
                        conn.commit()
                    st.success("تم تحديث الطلب بنجاح!")
                    st.rerun()