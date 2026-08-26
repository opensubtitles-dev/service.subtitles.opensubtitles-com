
import os
import struct

import xbmcvfs, xbmc

from urllib.parse import unquote
from resources.lib.utilities import log


def get_file_data(file_original_path):
    item = {"temp": False, "rar": False, "file_original_path": file_original_path}
    log(__name__, f"Processing item: {item}")


    if file_original_path.find("http") > -1:
        orig_path = xbmc.getInfoLabel('Window(10000).Property(videoinfo.current_path)')
        orig_size = xbmc.getInfoLabel('Window(10000).Property(videoinfo.current_size)')
        orig_oshash = xbmc.getInfoLabel('Window(10000).Property(videoinfo.current_oshash)')
        if orig_path:
            orig_path = str(orig_path)
            item["basename"] = os.path.basename(orig_path)
            item["file_original_path"] = orig_path
        if orig_size:
            item["file_size"] = int(orig_size)
        if orig_oshash:
            item["moviehash"] = orig_oshash

        if any((orig_path, orig_size, orig_oshash)):
            return item

        item["temp"] = True

    elif file_original_path.find("rar://") > -1:
        item["rar"] = True
        item["file_original_path"] = os.path.dirname(file_original_path[6:])
        item["basename"] = os.path.basename(file_original_path)

    elif file_original_path.find("stack://") > -1:
        stack_path = file_original_path.split(" , ")
        item["file_original_path"] = stack_path[0][8:]

    if not item["temp"]:
        # basename from the NORMALIZED path. The old unconditional [6:] slice
        # (meant to drop a "rar://" prefix) ate the first six characters of
        # every plain local path and mangled short ones ("/tv/E1.mkv" ->
        # ".mkv"), degrading the fallback search query and smart ranking.
        # The rar branch above already set its basename from the vfs path.
        if "basename" not in item:
            item["basename"] = os.path.basename(item["file_original_path"])
        # Hashing is an enhancer, never a gate: a rar probe error or vfs
        # hiccup must degrade to a hashless name/id search, not abort it.
        try:
            item["file_size"], item["moviehash"] = hash_file(item["file_original_path"], item["rar"])
        except Exception as e:
            log(__name__, f"Hashing failed ({e!r}), continuing without moviehash")
    return item


def hash_file(file_path, rar):
    log(__name__, f"Processing file: {file_path} - Is RAR: {rar}")

    if rar:
        # The rar VFS uses the following scheme: rar://urlencoded_rar_path/archive_content
        # file_path is thus urlencoded at this point and must be unquoted
        return hash_rar(unquote(file_path))

    log(__name__, "Hash Standard file")
    long_long_format = "q"  # long long
    byte_size = struct.calcsize(long_long_format)
    with xbmcvfs.File(file_path) as f:
        file_size = f.size()
        hash_ = file_size

        if file_size < 65536 * 2:
            # Too small for the OpenSubtitles hash (needs a 64KiB head + tail).
            # Return the (size, hash) shape the caller unpacks - the old scalar
            # "SizeError" sentinel raised ValueError there and killed the whole
            # search instead of letting it fall back to a name/id lookup.
            log(__name__, f"File too small for moviehash ({file_size} bytes), continuing without hash")
            return file_size, ""

        buffer = f.readBytes(65536)
        f.seek(max(0, file_size - 65536), 0)
        buffer += f.readBytes(65536)
        f.close()

    for x in range(int(65536 / byte_size) * 2):
        size = x * byte_size
        (l_value,) = struct.unpack(long_long_format, buffer[size:size + byte_size])
        hash_ += l_value
        hash_ = hash_ & 0xFFFFFFFFFFFFFFFF

    return_hash = "%016x" % hash_
    return file_size, return_hash

def hash_rar(first_rar_file):
    log(__name__, "Hash Rar file")
    f = xbmcvfs.File(first_rar_file)
    a = f.readBytes(4)
    log(__name__, "Hash Rar a: %s" % a)
    # Ensure comparison is done with a byte string
    if a != b"Rar!":
        raise Exception("ERROR: This is not rar file.")
    
    seek = 0
    for i in range(4):
        f.seek(max(0, seek), 0)
        a = f.readBytes(100)
        type_, flag, size = struct.unpack("<BHH", a[2:2 + 5])
        
        if 0x74 == type_:
            if 0x30 != struct.unpack("<B", a[25:25 + 1])[0]:
                raise Exception("Bad compression method! Work only for 'store'.")
            
            s_divide_body_start = seek + size
            s_divide_body, s_unpack_size = struct.unpack("<II", a[7:7 + 2 * 4])
            
            if flag & 0x0100:
                s_unpack_size = (struct.unpack("<I", a[36:36 + 4])[0] << 32) + s_unpack_size
                log(__name__, "Hash untested for files bigger that 2gb. May work or may generate bad hash.")
            
            last_rar_file = get_last_split(first_rar_file, (s_unpack_size - 1) / s_divide_body)
            hash_ = add_file_hash(first_rar_file, s_unpack_size, s_divide_body_start)
            hash_ = add_file_hash(last_rar_file, hash_, (s_unpack_size % s_divide_body) + s_divide_body_start - 65536)
            f.close()
            return s_unpack_size, "%016x" % hash_
        
        seek += size
    
    raise Exception("ERROR: Not Body part in rar file.")

def get_last_split(first_rar_file, x):
    if first_rar_file[-3:] == "001":
        return first_rar_file[:-3] + ("%03d" % (x + 1))
    if first_rar_file[-11:-6] == ".part":
        return first_rar_file[0:-6] + ("%02d" % (x + 1)) + first_rar_file[-4:]
    if first_rar_file[-10:-5] == ".part":
        return first_rar_file[0:-5] + ("%1d" % (x + 1)) + first_rar_file[-4:]
    return first_rar_file[0:-2] + ("%02d" % (x - 1))


def add_file_hash(name, hash_, seek):
    f = xbmcvfs.File(name)
    f.seek(max(0, seek), 0)
    for i in range(8192):
        hash_ += struct.unpack("<q", f.readBytes(8))[0]
        hash_ = hash_ & 0xffffffffffffffff
    f.close()
    return hash_
