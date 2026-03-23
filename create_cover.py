#!/usr/bin/env python3
"""
创建简单的默认封面图
"""
import struct
import zlib


def create_simple_cover():
    """创建一个简单的蓝色封面图"""
    # 图片尺寸
    width, height = 900, 383
    
    # 创建蓝色背景的像素数据
    # 蓝色: RGB(26, 115, 232) = #1a73e8
    pixel_data = []
    for y in range(height):
        row = []
        for x in range(width):
            # 蓝色背景
            row.extend([26, 115, 232])  # RGB
        pixel_data.extend(row)
    
    # 创建 PNG 文件
    def create_png(filename, width, height, pixels):
        def png_chunk(chunk_type, data):
            chunk = chunk_type + data
            crc = zlib.crc32(chunk) & 0xffffffff
            return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)
        
        # PNG 签名
        signature = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr = png_chunk(b'IHDR', ihdr_data)
        
        # IDAT chunk (图像数据)
        # 为每一行添加过滤器字节 (0 = 无过滤)
        raw_data = b''
        for y in range(height):
            raw_data += b'\x00'  # 过滤器字节
            for x in range(width):
                idx = (y * width + x) * 3
                raw_data += bytes([pixels[idx], pixels[idx+1], pixels[idx+2]])
        
        compressed = zlib.compress(raw_data, 9)
        idat = png_chunk(b'IDAT', compressed)
        
        # IEND chunk
        iend = png_chunk(b'IEND', b'')
        
        # 写入文件
        with open(filename, 'wb') as f:
            f.write(signature)
            f.write(ihdr)
            f.write(idat)
            f.write(iend)
    
    # 创建封面图
    cover_path = "cover.png"
    create_png(cover_path, width, height, bytes(pixel_data))
    print(f"[OK] 封面图已创建: {cover_path}")
    return cover_path


if __name__ == "__main__":
    create_simple_cover()
