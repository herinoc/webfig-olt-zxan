# app/models.py
import requests

def get_all_olt_data(db):
    cursor = db.cursor(dictionary=True)  # optional: biar hasilnya dict
    cursor.execute("SELECT * FROM table_olt")
    result = cursor.fetchall()
    cursor.close()
    return result

def get_olt_by_id(id_olt):
    try:
        response = requests.get("http://localhost:5000/api/list_olt")
        if response.status_code == 200:
            data = response.json()
            return next((olt for olt in data if olt["id_olt"] == id_olt), None)
        else:
            print(f"Gagal ambil data OLT. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Terjadi kesalahan saat mengambil data OLT: {e}")
        return None