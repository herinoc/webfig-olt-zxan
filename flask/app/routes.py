# --------------------- IMPORT MODULE ---------------------------
from flask import Blueprint, current_app, render_template, request, jsonify, send_file
from app.models import get_all_olt_data
from app.db import get_db_connection
from app.olt.remote_olt import remote_telnet_to_olt
from app.models import get_olt_by_id  # kamu bisa ganti dengan DB query
import asyncio
from datetime import datetime
import random, string
from app.olt.remote_olt import telnet_show_uncfg_onu, telnet_show_onu_state, config_onu_telnet, config_onu_bridge_telnet
from app.exporter import export_onu_history_to_excel
import os

# from app.olt.remote_olt import proses_limitasi
# from app.olt.remote_olt import do_telnet, read_command  # pastikan impor sesuai lokasi kamu

import mysql.connector

main = Blueprint('main', __name__)

# --------------------- TAMPILKAN DI INDEX.HTML ---------------------------

@main.route('/')
def index():
    conn = None
    data = []
    try:
        conn = get_db_connection()
        data = get_all_olt_data(conn)
    except Exception as e:
        current_app.logger.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    return render_template('index.html', data=data)

#@main.route('/')
#def index():
#    # Ambil konfigurasi dari app
#    db_config = current_app.config['DB_CONFIG']
#    print(db_config)
#    # Bikin koneksi baru
#    db = mysql.connector.connect(**db_config)
#    
#    # Ambil data
#    data = get_all_olt_data(db)
#    
#    db.close()  # Penting! Tutup koneksi setelah dipakai
#    
#    return render_template('index.html', data=data)

# --------------------------- INSERT DATABASE ------------------------------
@main.route('/api/add_olt', methods=['POST'])
def api_add_olt():
    try:
        # Ambil data dari body JSON
        data = request.get_json()

        # Mapping field sesuai JS (nama key JSON harus cocok!)
        ip = data.get('ip_address')
        vlan = data.get('vlan')
        jenis = data.get('jenis_olt')
        alamat = data.get('alamat_pop')
        username = data.get('username_telnet')
        password = data.get('password_telnet')

        # Validasi input
        if not all([ip, vlan, jenis, alamat, username, password]):
            return jsonify({'message': 'Data tidak lengkap'}), 400

        # Koneksi ke DB
        db = get_db_connection()
        cursor = db.cursor()

        # Simpan ke DB
        sql = """
            INSERT INTO table_olt 
            (ip_address, vlan, jenis_olt, alamat_pop, username_telnet, password_telnet) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (ip, vlan, jenis, alamat, username, password))
        db.commit()

        new_id = cursor.lastrowid

        # Tutup koneksi
        cursor.close()
        db.close()

        return jsonify({
            'message': 'OLT data saved successfully',
            'id_olt': new_id
        }), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 500


# -------------------------- SELECT DATABASE -------------------------------
@main.route('/api/list_olt')
def list_olt():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt")
    # cursor.execute("SELECT ip_address, vlan, jenis_olt, alamat_pop FROM table_olt")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

# -------------------------- UPDATE DATABASE -------------------------------
@main.route('/api/update_olt', methods=['POST'])
def update_olt():
    id_olt = request.form.get('idOlt')
    if not id_olt:
        return jsonify({"error": "ID OLT tidak ditemukan"}), 400

    ip_address = request.form.get('ipAddress', '')
    vlan = request.form.get('vlan', '')
    jenis_olt = request.form.get('jenisOlt', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        UPDATE table_olt SET
        ip_address = %s,
        vlan = %s,
        jenis_olt = %s,
        username_telnet = %s,
        password_telnet = %s
        WHERE id_olt = %s
    """

    try:
        cursor.execute(sql, (ip_address, vlan, jenis_olt, username, password, id_olt))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": f"Error saat update: {str(e)}"}), 500

    cursor.close()
    conn.close()
    return jsonify({"message": "Data berhasil diupdate"}), 200

# -------------------------- API KONEKSi TELNET -------------------------------

@main.route('/api/send_tcont_command', methods=['POST'])
def send_tcont_command():
    data = request.get_json()
    profile_name = data.get('profileName')
    fixed_value = data.get('fixedValue')  # untuk upload
    pir = data.get('pir')                  # untuk download
    sir = data.get('sir')                  # untuk download
    id_olt = data.get('id_olt')            # harus dikirim dari frontend
    mode = data.get('mode', 'fixed')  # default: fixed

    if not id_olt:
        return jsonify({'output': 'ID OLT harus disertakan'}), 400
    if not profile_name:
        return jsonify({'output': 'profileName harus diisi'}), 400

    # Ambil data OLT berdasarkan id_olt
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
    olt_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not olt_data:
        return jsonify({'output': 'OLT tidak ditemukan'}), 404

    import asyncio
    from app.olt.remote_olt import telnet_send_tcont_command, telnet_send_traffic_command

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        output = ""

        # upload profile (tcont)
        if fixed_value is not None:
            output += "\n"
            output += loop.run_until_complete(
                telnet_send_tcont_command(olt_data, profile_name, fixed_value, mode)
            )

        # download profile (traffic) hanya untuk C300
        if pir is not None and sir is not None:
            if olt_data.get('jenis_olt') != 'C300':
                output += "\nPerintah traffic profile tidak didukung pada jenis OLT ini."
            else:
                output += "\n"
                output += loop.run_until_complete(
                    telnet_send_traffic_command(olt_data, profile_name, pir, sir)
                )

        if not output:
            return jsonify({'output': 'Parameter fixedValue atau pir & sir harus diisi'}), 400

        return jsonify({'output': output})

    except Exception as e:
        return jsonify({'output': f'Gagal koneksi Telnet: {str(e)}'}), 500
    finally:
        loop.close()


@main.route("/api/telnet_olt", methods=["POST"])
def telnet_olt():
    data = request.get_json()
    id_olt = data.get("id_olt")

    # Validasi ID
    if not id_olt:
        return jsonify({"output": "ID OLT tidak dikirim"}), 400

    # Ambil data OLT dari database (atau dummy JSON)
    olt_data = get_olt_by_id(int(id_olt))
    if not olt_data:
        return jsonify({"output": "OLT tidak ditemukan"}), 404

    try:
        output = remote_telnet_to_olt(olt_data)
        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"output": f"Telnet gagal: {str(e)}"}), 500

# -------------------------- KONEKSI ONU TYPE -------------------------------

@main.route('/api/show_onu_type_print', methods=['POST'])
def show_onu_type_print():
    data = request.get_json()
    id_olt = data.get('id_olt')

    if not id_olt:
        return jsonify({'output': 'ID OLT harus dikirim'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
    olt_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not olt_data:
        return jsonify({'output': 'OLT tidak ditemukan'}), 404

    import asyncio
    from app.olt.remote_olt import telnet_show_onu_type

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        output = loop.run_until_complete(
            telnet_show_onu_type(olt_data)
        )
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'output': f'Gagal Telnet: {str(e)}'}), 500
    finally:
        loop.close()

# --------------------- KONEKSI FORM PSB 3 SELECTED----------------------

@main.route('/api/show_profiles_and_onu', methods=['POST'])
def show_profiles_and_onu():
    data = request.get_json()
    id_olt = data.get('id_olt')

    if not id_olt:
        return jsonify({'error': 'ID OLT harus dikirim'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
    olt_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not olt_data:
        return jsonify({'error': 'OLT tidak ditemukan'}), 404

    import asyncio
    from app.olt.remote_olt import telnet_show_onu_type, do_telnet

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # ambil ONU type
        onu_output = loop.run_until_complete(telnet_show_onu_type(olt_data))
        onu_types = [l.strip() for l in onu_output.splitlines() if l.strip()]

        # ambil profile upload & download
        profiles_output = loop.run_until_complete(do_telnet(olt_data))
        lines = profiles_output.splitlines()
        upload_profiles = []
        download_profiles = []
        mode = None
        for line in lines:
            line = line.strip()
            if line.startswith('UPLOAD'):
                mode = 'upload'
                continue
            if line.startswith('DOWNLOAD'):
                mode = 'download'
                continue
            if not line:
                continue
            if mode == 'upload':
                upload_profiles.append(line)
            elif mode == 'download':
                download_profiles.append(line)

        return jsonify({
            'onu_types': onu_types,
            'upload_profiles': upload_profiles,
            'download_profiles': download_profiles
        })
    except Exception as e:
        return jsonify({'error': f'Gagal ambil data: {e}'}), 500
    finally:
        loop.close()

#  --------------------- ENDPOINT GET SN DAN PORT OLT----------------------

@main.route('/api/show_uncfg_onu', methods=['GET', 'POST'])
def show_uncfg_onu():
    if request.method == 'GET':
        return jsonify({'message': 'Gunakan POST untuk mengirim data'})

    data = request.get_json()
    id_olt = data.get('id_olt')
    jenis_olt = data.get('jenis_olt')

    if not id_olt or not jenis_olt:
        return jsonify({'error': 'id_olt dan jenis_olt wajib dikirim'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
    olt_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not olt_data:
        return jsonify({'error': 'OLT tidak ditemukan'}), 404

    try:
        result = asyncio.run(telnet_show_uncfg_onu(olt_data, jenis_olt))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Gagal Telnet: {str(e)}'}), 500

# --------------------- ENDPONT FIND ONU ------------------------

@main.route('/api/check_empty_onu', methods=['POST'])
def check_empty_onu():
    data = request.get_json()
    id_olt = data.get('id_olt')
    jenis_olt = data.get('jenis_olt')
    port_olt = data.get('port_olt')  # contoh 1/3/3

    if not id_olt or not jenis_olt or not port_olt:
        return jsonify({'error': 'id_olt, jenis_olt, port_olt wajib dikirim'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
    olt_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not olt_data:
        return jsonify({'error': 'OLT tidak ditemukan'}), 404

    try:
        # panggil telnet_show_onu_state (sudah return dict)
        state_result = asyncio.run(telnet_show_onu_state(olt_data, jenis_olt, port_olt))
        used_slots = state_result['used_slots']
        free_slots = state_result['free_slots']

        # cari ONU kosong berikutnya (slot terkecil)
        next_onu = free_slots[0] if free_slots else None

        return jsonify({
            'used_onu': used_slots,         # daftar slot terpakai
            'empty_onu': free_slots,        # daftar slot kosong
            'next_onu': next_onu,           # slot kosong berikutnya
            'raw_output': state_result['raw_output'],
            'matches_found': state_result['matches_found']
        })
    except Exception as e:
        return jsonify({'error': f'Gagal Telnet: {str(e)}'}), 500


# -------------------------- ENDPONT SARING ONU IDLE -----------------------
@main.route('/api/show_onu_state', methods=['POST'])
def show_onu_state():
    data = request.get_json()
    id_olt = data.get('id_olt')
    jenis_olt = data.get('jenis_olt')
    onu_index = data.get('onu_index')  # misal "1/5/11"

    # ambil data OLT dari DB (sama seperti endpoint show_uncfg_onu)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
    olt_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not olt_data:
        return jsonify({'error': 'OLT tidak ditemukan'}), 404

    result = asyncio.run(telnet_show_onu_state(olt_data, jenis_olt, onu_index))
    return jsonify(result)

# -------------------------- ENDPOINT CONFIG PROSES --------------------------

# @main.route('/api/config_onu', methods=['POST'])
# def config_onu():
#     data = request.get_json(force=True)
#     current_app.logger.info(f"Payload diterima: {data}")

#     id_olt = data.get('id_olt')
#     jenis_olt = data.get('jenis_olt')
#     port_base = data.get('port_base')
#     onu_num = data.get('onu_num')

#     if not port_base or not onu_num:
#         return jsonify({'error': 'port_base/onu_num tidak ada di payload'}), 400

#     lan_lock = data.get('lock')  # ambil sesuai nama key yg dikirim

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
#     olt_data = cursor.fetchone()
#     cursor.close()
#     conn.close()

#     if not olt_data:
#         return jsonify({'error': 'OLT tidak ditemukan'}), 404

#     result = asyncio.run(config_onu_telnet(
#         olt_data,
#         jenis_olt,
#         port_base,
#         onu_num,
#         data.get('jenis_modem'),
#         data.get('sn'),
#         data.get('nama_pelanggan'),
#         data.get('alamat'),
#         data.get('upload_profile'),
#         data.get('download_profile'),
#         data.get('vlan'),
#         data.get('pppoe_username'),
#         data.get('pppoe_password'),
#         lan_lock=lan_lock  # kirim ke fungsi telnet
#     ))

#     return jsonify({'status': 'ok', 'output': result})

def generate_kode_psb():
    return "PSB" + ''.join(random.choices(string.digits, k=6))

@main.route('/api/config_onu', methods=['POST'])
def config_onu():
    data = request.get_json(force=True)
    current_app.logger.info(f"Payload diterima: {data}")

    id_olt = data.get('id_olt')
    jenis_olt = data.get('jenis_olt')
    port_base = data.get('port_base')
    onu_num = data.get('onu_num')

    if not port_base or not onu_num:
        return jsonify({'error': 'port_base/onu_num tidak ada di payload'}), 400

    lan_lock = data.get('lock')  # ambil sesuai nama key yg dikirim

    # ambil data olt
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
    olt_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not olt_data:
        return jsonify({'error': 'OLT tidak ditemukan'}), 404

    # jalankan telnet config
    result = asyncio.run(config_onu_telnet(
        olt_data,
        jenis_olt,
        port_base,
        onu_num,
        data.get('jenis_modem'),
        data.get('sn'),
        data.get('nama_pelanggan'),
        data.get('alamat'),
        data.get('upload_profile'),
        data.get('download_profile'),
        data.get('vlan'),
        data.get('pppoe_username'),
        data.get('pppoe_password'),
        lan_lock=lan_lock  # kirim ke fungsi telnet
    ))

    # generate kode_psb unik, misal: PSB-20250922-XXXX
    import datetime, random
    kode_psb = f"PSB-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

    # simpan hasil ke tabel config_onu_history
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO config_onu_history (
            kode_psb, id_olt, jenis_olt, port_base, onu_num, jenis_modem, sn,
            nama_pelanggan, alamat, upload_profile, download_profile, vlan,
            pppoe_username, pppoe_password, lan_lock, status, created_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """, (
        kode_psb,
        id_olt,
        jenis_olt,
        port_base,
        onu_num,
        data.get('jenis_modem'),
        data.get('sn'),
        data.get('nama_pelanggan'),
        data.get('alamat'),
        data.get('upload_profile'),
        data.get('download_profile'),
        data.get('vlan'),
        data.get('pppoe_username'),
        data.get('pppoe_password'),
        lan_lock,
        'ok'  # status (misalnya ok)
    ))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'ok', 'kode_psb': kode_psb, 'output': result})

# ------------------------ READ DATA PSB ----------------------------------

@main.route('/api/get_report_data', methods=['GET'])
def get_report_data():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT nama_pelanggan, alamat, sn, port_base, onu_num, vlan,
                   upload_profile, download_profile, pppoe_username,
                   pppoe_password, lan_lock, created_at
            FROM config_onu_history
            ORDER BY created_at DESC
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        return jsonify(results), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching report data: {e}")
        return jsonify({'message': 'Database error', 'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# --------------------------- CONFIG BRIDGE -----------------------------

@main.route('/api/config_onu_bridge', methods=['POST'])
def config_onu_bridge():
    data = request.get_json(force=True)
    current_app.logger.info(f"Payload diterima (Bridge): {data}")

    id_olt    = data.get('id_olt')
    jenis_olt = data.get('jenis_olt')
    port_base = data.get('port_base')
    onu_num   = data.get('onu_num')

    if not port_base or not onu_num:
        return jsonify({'error': 'port_base/onu_num tidak ada di payload'}), 400

    # Ambil data OLT
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_olt WHERE id_olt = %s", (id_olt,))
    olt_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not olt_data:
        return jsonify({'error': 'OLT tidak ditemukan'}), 404

    # Jalankan telnet config – pakai fungsi khusus bridge
    try:
        result = asyncio.run(config_onu_bridge_telnet(
            olt_data,
            jenis_olt,
            port_base,
            onu_num,
            data.get('jenis_modem'),
            data.get('sn'),
            data.get('nama_pelanggan'),
            data.get('alamat'),
            data.get('upload_profile'),
            data.get('download_profile'),
            data.get('vlan')
        ))
        status = 'ok'
    except Exception as e:
        current_app.logger.error(f"Telnet Bridge gagal: {e}")
        result = f"ERROR: {e}"
        status = 'fail'

    # Generate kode unik untuk bridge
    import datetime, random
    kode_psb = f"BRIDGE-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

    # Simpan hasil ke tabel history
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO config_onu_history (
            kode_psb, id_olt, jenis_olt, port_base, onu_num, jenis_modem, sn,
            nama_pelanggan, alamat, upload_profile, download_profile, vlan,
            pppoe_username, pppoe_password, lan_lock, status, created_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """, (
        kode_psb,
        id_olt,
        jenis_olt,
        port_base,
        onu_num,
        data.get('jenis_modem'),
        data.get('sn'),
        data.get('nama_pelanggan'),
        data.get('alamat'),
        data.get('upload_profile'),
        data.get('download_profile'),
        data.get('vlan'),
        None,  # username PPPoE kosong
        None,  # password PPPoE kosong
        None,  # LAN lock kosong
        'ok'
    ))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'ok', 'kode_psb': kode_psb, 'output': result})

# --------------------- EXPORT KE EXCEL ---------------------------
@main.route("/api/export_excel")
def export_excel():
    conn = None
    buf = None
    try:
        conn = get_db_connection()
        buf = export_onu_history_to_excel(conn)
    except Exception as e:
        current_app.logger.error(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
    return send_file(buf, as_attachment=True, download_name="config_onu_history.xlsx")
