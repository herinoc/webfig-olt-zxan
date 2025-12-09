import asyncio
import telnetlib3
import re

# ------------------------ SAFE READ ------------------------
async def safe_read(reader, timeout=1):
    try:
        return await asyncio.wait_for(reader.read(4096), timeout=timeout)
    except asyncio.TimeoutError:
        return ''

# ------------------------ READ ALL OUTPUT (menunggu idle) ------------------------
async def read_all_output(reader, writer, command=None, max_wait=60, idle_timeout=2):
    """
    Kirim perintah dan baca semua output sampai tidak ada data baru idle_timeout detik
    atau sampai max_wait tercapai.
    """
    if command:
        writer.write(command + "\n")

    output = ""
    start = asyncio.get_event_loop().time()

    while True:
        try:
            chunk = await asyncio.wait_for(reader.read(4096), timeout=idle_timeout)
        except asyncio.TimeoutError:
            # tidak ada data baru dalam idle_timeout detik => selesai
            break

        if chunk:
            output += chunk

        if asyncio.get_event_loop().time() - start > max_wait:
            break

    return output

# ------------------------ TELNET LOGIN ------------------------
async def telnet_login(olt_data):
    """Login Telnet, kembalikan reader, writer"""
    ip = olt_data['ip_address']
    username = olt_data['username_telnet']
    password = olt_data['password_telnet']

    reader, writer = await telnetlib3.open_connection(host=ip, port=23, shell=None)

    # proses login
    while True:
        chunk = await safe_read(reader, timeout=5)
        if not chunk:
            break
        if "Username:" in chunk:
            writer.write(username + "\r")
        elif "Password:" in chunk:
            writer.write(password + "\r")
            break

    # tunggu prompt utama
    while True:
        chunk = await safe_read(reader, timeout=5)
        if "#" in chunk:
            break

    # matikan paging di semua platform (C300, C600)
    for cmd in ("terminal length 0", "screen-length 0"):
        writer.write(cmd + "\n")
        await asyncio.sleep(0.3)
        await safe_read(reader, timeout=1)

    return reader, writer

# ------------------------ DO TELNET (SHOW PROFILES) ------------------------

# async def do_telnet(olt_data):
#     reader, writer = await telnet_login(olt_data)

#     # Upload profiles
#     tcont_output = await read_all_output(reader, writer, "show gpon profile tcont")
#     upload_result = ["UPLOAD (T-CONT Profile) :"]
#     blocks = tcont_output.split("Profile name")
#     for block in blocks[1:]:
#         lines = block.strip().splitlines()
#         if lines:
#             name = lines[0].replace(":", "").strip()
#             upload_result.append(name)

#     # Download profiles hanya untuk C300
#     download_result = []
#     if olt_data.get('jenis_olt') == 'C300':
#         traffic_output = await read_all_output(
#             reader,
#             writer,
#             "show gpon profile traffic",
#             max_wait=180,
#             idle_timeout=8
#         )
#         download_result = ["\nDOWNLOAD (Traffic Profile) :"]
#         pattern = re.compile(r"profile name\s*:\s*(\S+)", re.IGNORECASE)
#         for match in pattern.finditer(traffic_output):
#             download_result.append(match.group(1))
#     else:
#         download_result = ["\nDOWNLOAD (Traffic Profile) : Tidak didukung jenis OLT ini"]

#     writer.write("exit\n")
#     await asyncio.sleep(0.5)
#     writer.close()

#     return "\n".join(upload_result + [""] + download_result)


#     # Tutup koneksi
#     writer.write("exit\n")
#     await asyncio.sleep(0.5)
#     writer.close()

#     return "\n".join(upload_result + [""] + download_result)

# ------------------------ DO TELNET (SHOW PROFILES) ------------------------
async def do_telnet(olt_data):
    reader, writer = await telnet_login(olt_data)

    # Upload profiles
    tcont_output = await read_all_output(reader, writer, "show gpon profile tcont")
    upload_result = ["UPLOAD (T-CONT Profile) :"]
    blocks = tcont_output.split("Profile name")
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        if lines:
            name = lines[0].replace(":", "").strip()
            upload_result.append(name)

    # Download / Traffic Profiles
    download_result = []
    jenis = olt_data.get('jenis_olt', '').upper()

    if jenis == 'C300':
        # Command lama
        traffic_output = await read_all_output(
            reader,
            writer,
            "show gpon profile traffic",
            max_wait=180,
            idle_timeout=8
        )
        download_result = ["\nDOWNLOAD (Traffic Profile) :"]
        pattern = re.compile(r"profile name\s*:\s*(\S+)", re.IGNORECASE)
        for match in pattern.finditer(traffic_output):
            download_result.append(match.group(1))

    elif jenis == 'C600':
        # Command baru
        qos_output = await read_all_output(
            reader,
            writer,
            "show qos traffic-profile",
            max_wait=180,
            idle_timeout=8
        )
        download_result = ["\nDOWNLOAD (Traffic Profile) :"]
        # Ambil nama setelah 'profile :'
        pattern = re.compile(r'profile\s*:\s*([A-Za-z0-9\-\_]+)', re.IGNORECASE)
        for match in pattern.finditer(qos_output):
            download_result.append(match.group(1))
    else:
        download_result = ["\nDOWNLOAD (Traffic Profile) : Tidak didukung jenis OLT ini"]

    # Tutup koneksi
    writer.write("exit\n")
    await asyncio.sleep(0.5)
    writer.close()

    return "\n".join(upload_result + [""] + download_result)

# -------------------- BATAS PERBAIKAN -----------------------

def remote_telnet_to_olt(olt_data):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(do_telnet(olt_data))

# ------------------------ TCONT UPLOAD ------------------------
async def telnet_send_tcont_command(olt_data, profile_name, fixed_value, mode='fixed'):
    reader, writer = await telnet_login(olt_data)

    # Masuk konfigurasi
    writer.write("conf t\n")
    await asyncio.sleep(0.5)
    writer.write("gpon\n")
    await asyncio.sleep(0.5)

    output = ""

    if mode == 'fixed':
        cmd = f"profile tcont {profile_name} type 1 fixed {fixed_value}\n"
        writer.write(cmd)
        await asyncio.sleep(0.5)
        output += await read_all_output(reader, writer, "", max_wait=10)

    elif mode == 'mbw':
        match = re.search(r'(\d+)MB', profile_name)
        if match:
            mb_value = int(match.group(1))
            pir = mb_value * 1024
            sir = pir // 2
            cmd = f"profile tcont {profile_name} type 3 assured {sir} maximum {pir}\n"
            writer.write(cmd)
            await asyncio.sleep(0.5)
            output += await read_all_output(reader, writer, "", max_wait=10)

    # Keluar konfigurasi
    writer.write("end\n")
    await asyncio.sleep(0.5)
    output += await read_all_output(reader, writer, "", max_wait=5)

    writer.write("exit\n")
    await asyncio.sleep(0.5)
    writer.close()
    return output.strip()

# ------------------------ TCONT / TRAFFIC DOWNLOAD ------------------------
async def telnet_send_traffic_command(olt_data, profile_name, pir, sir):
    reader, writer = await telnet_login(olt_data)

    # Masuk konfigurasi
    writer.write("conf t\n")
    await asyncio.sleep(0.5)
    writer.write("gpon\n")
    await asyncio.sleep(0.5)

    cmd = f"profile traffic {profile_name} sir {sir} pir {pir}\n"
    writer.write(cmd)
    await asyncio.sleep(0.5)
    output = await read_all_output(reader, writer, "", max_wait=10)

    # Keluar konfigurasi
    writer.write("end\n")
    await asyncio.sleep(0.5)
    output += "\n" + await read_all_output(reader, writer, "", max_wait=5)

    writer.write("exit\n")
    await asyncio.sleep(0.5)
    writer.close()
    return output.strip()

# ------------------------ SHOW ONU TYPE ------------------------
async def telnet_show_onu_type(olt_data):
    reader, writer = await telnet_login(olt_data)
    output = await read_all_output(
        reader,
        writer,
        "show onu-type gpon",
        max_wait=120,
        idle_timeout=5
    )

    writer.write("exit\n")
    await asyncio.sleep(0.5)
    writer.close()

    # Parsing nama ONU
    parsed_output = ""
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("ONU type name:"):
            parsed_output += line.replace("ONU type name:", "").strip() + "\n"

    return parsed_output.strip()

# ------------------------ SHOW UNCONFIGURED ONU ------------------------
async def telnet_show_uncfg_onu(olt_data, jenis_olt):
    reader, writer = await telnet_login(olt_data)

    if jenis_olt.upper() in ["C300", "C320"]:
        command = "show gpon onu uncfg"
    elif jenis_olt.upper() == "C600":
        command = "show pon onu uncfg"
    else:
        command = "show gpon onu uncfg"

    output = await read_all_output(reader, writer, command, max_wait=120, idle_timeout=5)

    writer.write("exit\n")
    await asyncio.sleep(0.5)
    writer.close()

    sn_list = []
    index_list = []

    for line in output.splitlines():
        line = line.strip()
        # --- format C300/C320 lama ---
        if line.startswith("gpon-onu") or line.startswith("pon-onu"):
            parts = line.split()
            if len(parts) >= 2:
                raw_index = parts[0]  # gpon-onu_1/3/3:1
                try:
                    inner = raw_index.split("_", 1)[1]  # 1/3/3:1
                    onu_index = inner.split(":", 1)[0]  # 1/3/3
                except Exception:
                    onu_index = ""
                sn_list.append(parts[1])
                index_list.append(onu_index)

        # --- format C600 baru ---
        elif line.startswith("gpon_olt-"):
            parts = line.split()
            if len(parts) >= 2:
                raw_index = parts[0]  # gpon_olt-1/1/14
                try:
                    # ambil setelah tanda - supaya hasilnya 1/1/14
                    onu_index = raw_index.split("-", 1)[1]
                except Exception:
                    onu_index = ""
                sn_list.append(parts[1])  # SN ada di kolom kedua
                index_list.append(onu_index)

    return {"sn_list": sn_list, "index_list": index_list}


# async def telnet_show_uncfg_onu(olt_data, jenis_olt):
#     reader, writer = await telnet_login(olt_data)

#     if jenis_olt.upper() in ["C300", "C320"]:
#         command = "show gpon onu uncfg"
#     elif jenis_olt.upper() == "C600":
#         command = "show pon onu uncfg"
#     else:
#         command = "show gpon onu uncfg"

#     output = await read_all_output(reader, writer, command, max_wait=120, idle_timeout=5)

#     writer.write("exit\n")
#     await asyncio.sleep(0.5)
#     writer.close()

#     # Parsing SN + OnuIndex
#     sn_list = []
#     index_list = []
#     for line in output.splitlines():
#         line = line.strip()
#         if line.startswith("gpon-onu") or line.startswith("pon-onu"):
#             parts = line.split()
#             if len(parts) >= 2:
#                 # contoh parts[0] = gpon-onu_1/3/3:1
#                 # ambil yang di antara _ dan : supaya hasilnya 1/3/3
#                 raw_index = parts[0]
#                 try:
#                     inner = raw_index.split("_", 1)[1]  # 1/3/3:1
#                     onu_index = inner.split(":", 1)[0]  # 1/3/3
#                 except Exception:
#                     onu_index = ""

#                 sn_list.append(parts[1])
#                 index_list.append(onu_index)

#     return {"sn_list": sn_list, "index_list": index_list}

# ------------------- FUNGSI GET ONU IDLE -----------------------

def _extract_port_base(s):
    """
    Ambil pola 'd+/d+/d+' dari string apa pun.
    Contoh input yang mungkin:
      - "1/3/3:44" -> "1/3/3"
      - "gpon-onu_1/3/3:1" -> "1/3/3"
      - "gpon-olt_1/3/3" -> "1/3/3"
    """
    if s is None:
        return ""
    s = str(s).strip()
    m = re.search(r"(\d+/\d+/\d+)", s)
    if m:
        return m.group(1)
    # fallback: jika ada :, ambil bagian sebelum :
    if ":" in s:
        return s.split(":", 1)[0].strip()
    return s

# ANSI escape removal regex
_ANSI_RE = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

async def telnet_show_onu_state(olt_data, jenis_olt, onu_index):
    """
    Ambil state ONU di port (contoh onu_index = "1/3/11") lalu kembalikan used & free slots.
    Mengembalikan dict: { used_slots: [...], free_slots: [...], raw_output: "...", matches_found: N }
    """
    # pastikan kita only pass base port (1/3/3), bila user kirim 1/3/3:44 atau ada prefix, kita bersihkan
    base_onu_index = _extract_port_base(onu_index)

    reader, writer = await telnet_login(olt_data)

    # command tergantung jenis OLT
    if jenis_olt and jenis_olt.upper() in ["C300", "C320"]:
        command = f"show gpon onu state gpon-olt_{base_onu_index}"
    elif jenis_olt and jenis_olt.upper() == "C600":
        command = f"show gpon onu state gpon_olt-{base_onu_index}"
    else:
        command = f"show gpon onu state gpon-olt_{base_onu_index}"

    # kirim command dan baca output (read_all_output harus meng-handle paging jika perlu)
    output = await read_all_output(reader, writer, command, max_wait=120, idle_timeout=5)

    # close connection (santai)
    try:
        writer.write("exit\n")
    except Exception:
        pass
    await asyncio.sleep(0.2)
    try:
        writer.close()
    except Exception:
        pass

    # bersihkan output: hapus ANSI escape, normalisasi CRLF
    cleaned = _ANSI_RE.sub("", output)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # DEBUG: print output ke log Flask (cek di console)
    # print(f"=== RAW show_onu_state untuk {base_onu_index} ===\n{cleaned}\n=== END RAW ===")

    # Cari semua kemunculan '1/3/3:NN'
    used_indices = set()
    primary_pattern = re.compile(rf"{re.escape(base_onu_index)}:(\d+)")
    matches = primary_pattern.findall(cleaned)
    if matches:
        used_indices.update(int(x) for x in matches if x.isdigit())

    # fallback: jika primary tidak menemukan apa-apa, cari semua pola d+/d+/d+:\d+ dan filter yg port sama
    if not used_indices:
        alt_pattern = re.compile(r"(\d+/\d+/\d+):(\d+)")
        for port, num in alt_pattern.findall(cleaned):
            try:
                if port == base_onu_index and num.isdigit():
                    used_indices.add(int(num))
            except Exception:
                continue

    # filter nilai valid (1..128)
    used_indices = {i for i in used_indices if 1 <= i <= 128}

    free_slots = [i for i in range(1, 129) if i not in used_indices]

    return {
        "used_slots": sorted(list(used_indices)),
        "free_slots": free_slots,
        "raw_output": cleaned,
        "matches_found": len(used_indices)
    }

# ------------------------ PROSES CONFIG OLT  ------------------------

async def config_onu_telnet(
    olt_data, jenis_olt, port_base, onu_num,
    modem_type, sn, nama, alamat,
    upload_profile, download_profile, vlan,
    pppoe_user, pppoe_pass, lan_lock=None   # <— baru
):
    reader, writer = await telnet_login(olt_data)
    logs = ""

    # helper kirim command Telnet
    async def send(cmd, wait=0.5):
        if not isinstance(cmd, str):
            cmd = str(cmd)
        writer.write(cmd + "\n")
        await writer.drain()
        await asyncio.sleep(wait)

    if jenis_olt.upper() == "C600":
        # === PERINTAH C600 ===
        await send("conf t")
        await send(f"interface gpon_olt-{port_base}")
        await send(f"onu {onu_num} type {modem_type} sn {sn}")
        await send("exit")

        await send(f"interface gpon_onu-{port_base}:{onu_num}")
        await send(f"name {nama}")
        await send(f"description {alamat}")
        await send(f"tcont 1 name PPPOE profile {upload_profile}")
        await send(f"gemport 1 name PPPOE tcont 1")
        await send("exit")

        await send(f"interface vport-{port_base}.{onu_num}:1")
        await send(f"service-port 1 user-vlan {vlan} vlan {vlan}")
        await send(f"qos traffic-policy {download_profile} direction egress")
        await send("exit")

        await send(f"pon-onu-mng gpon_onu-{port_base}:{onu_num}")
        await send(f"service ServiceName gemport 1 vlan {vlan}")
        await send(
            f"wan-ip ipv4 mode pppoe username {pppoe_user} password {pppoe_pass} vlan-profile vlan{vlan} host 1"
        )
        if lan_lock == 'lock':
            await send("interface eth eth_0/1 state lock")
            await send("interface eth eth_0/2 state lock")
            await send("interface eth eth_0/3 state lock")
            await send("interface eth eth_0/4 state lock")
        elif lan_lock == 'open':
            await send("interface eth eth_0/1 state unlock")
            await send("interface eth eth_0/2 state unlock")
            await send("interface eth eth_0/3 state unlock")
            await send("interface eth eth_0/4 state unlock")
        await send("security-mgmt 2 ingress-type wan mode forward state enable protocol web")
        await send("exit")

    else:
        # === PERINTAH C300 / C320 ===
        await send(f"conf t")
        await send(f"interface gpon-olt_{port_base}")
        await send(f"onu {onu_num} type {modem_type} sn {sn}")
        await send("exit")

        await send(f"interface gpon-onu_{port_base}:{onu_num}")
        await send(f"name {nama}")
        await send(f"description {alamat}")
        await send(f"tcont 1 name PPPOE profile {upload_profile}")
        await send(f"gemport 1 name PPPOE tcont 1")
        await send(f"gemport 1 traffic-limit downstream {download_profile}")
        await send(f"encrypt 1 enable downstream")
        await send(f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}")
        await send(f"!")
        await send(f"pon-onu-mng gpon-onu_{port_base}:{onu_num}")
        await send(f"service ServiceName gemport 1 cos 0 vlan {vlan}")
        await send(
            f"wan-ip 1 mode pppoe username {pppoe_user} password {pppoe_pass} vlan-profile vlan{vlan} host 1"
        )
        if lan_lock == 'lock':
            await send("interface eth eth_0/1 state lock")
            await send("interface eth eth_0/2 state lock")
            await send("interface eth eth_0/3 state lock")
            await send("interface eth eth_0/4 state lock")
        elif lan_lock == 'open':
            await send("interface eth eth_0/1 state unlock")
            await send("interface eth eth_0/2 state unlock")
            await send("interface eth eth_0/3 state unlock")
            await send("interface eth eth_0/4 state unlock")
        await send(f"wan-ip 1 ping-response enable traceroute-response enable")
        await send(f"security-mgmt 1 state enable mode forward protocol web")
        await send(f"!")

    # tunggu output OLT
    await asyncio.sleep(1)
    logs += await read_all_output(reader, writer, "", max_wait=5)

    # tutup session
    writer.write("end\n")
    await writer.drain()
    await asyncio.sleep(0.5)
    writer.write("exit\n")
    await writer.drain()
    await asyncio.sleep(0.5)
    writer.close()

    return logs

# di remote_olt.py
async def telnet_show_profiles(olt_data):
    # login OLT
    tn = await telnet_login(olt_data)   # fungsi login kamu
    # kirim command yang sesuai
    tn.write(b"show traffic profile\n")
    output = await read_all_output(tn)
    tn.write(b"exit\n")
    tn.close()
    return output

# ---------------- CONFIG ONU BRIDGE -----------------

async def config_onu_bridge_telnet(
    olt_data, jenis_olt, port_base, onu_num,
    modem_type, sn, nama, alamat,
    upload_profile, download_profile, vlan
):
    reader, writer = await telnet_login(olt_data)

    # helper kirim command Telnet
    async def send(cmd, wait=0.5):
        if not isinstance(cmd, str):
            cmd = str(cmd)
        writer.write(cmd + "\n")
        await writer.drain()
        await asyncio.sleep(wait)

    if jenis_olt.upper() == "C600":
        # === PERINTAH C600 ===
        await send("conf t")
        await send(f"interface gpon_olt-{port_base}")
        await send(f"onu {onu_num} type {modem_type} sn {sn}")
        await send("exit")

        await send(f"interface gpon_onu-{port_base}:{onu_num}")
        await send(f"name {nama}")
        await send(f"description {alamat}")
        await send(f"tcont 1 name CIGNAL profile {upload_profile}")
        await send(f"gemport 1 name CIGNAL tcont 1")
        await send("exit")

        await send(f"interface vport-{port_base}.{onu_num}:1")
        await send(f"service-port 1 user-vlan {vlan} vlan {vlan}")
        await send(f"qos traffic-policy {download_profile} direction egress")
        await send("exit")

        await send(f"pon-onu-mng gpon_onu-{port_base}:{onu_num}")
        await send(f"service CIGNAL gemport 1 vlan {vlan}")
        for i in range(1, 5):
            await send(f"vlan port eth_0/{i} mode tag vlan {vlan}")
        await send("exit")

    else:
        # === PERINTAH C300 / C320 ===
        await send("conf t")
        await send(f"interface gpon-olt_{port_base}")
        await send(f"onu {onu_num} type {modem_type} sn {sn} vport-mode gemport")
        await send("exit")

        await send(f"interface gpon-onu_{port_base}:{onu_num}")
        await send(f"name {nama}")
        await send(f"description {alamat}")
        await send(f"tcont 1 name BRIDGE profile {upload_profile}")
        await send(f"gemport 1 name BRIDGE tcont 1")
        await send(f"gemport 1 traffic-limit downstream {download_profile}")
        await send(f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}")
        await send(f"port-identification format DSL-FORUM-PON vport 1")
        await send(f"pppoe-intermediate-agent enable vport 1")
        await send("exit")

        await send(f"pon-onu-mng gpon-onu_{port_base}:{onu_num}")
        await send(f"service BRIDGE gemport 1 vlan {vlan}")
        for i in range(1, 5):
            await send(f"vlan port eth_0/{i} mode tag vlan {vlan}")
        await send("exit")

    # tunggu output OLT
    await asyncio.sleep(1)
    logs = await read_all_output(reader, writer, "", max_wait=5)

    # tutup session
    await send("end", wait=0.5)
    await send("exit", wait=0.5)
    writer.close()

    return logs
