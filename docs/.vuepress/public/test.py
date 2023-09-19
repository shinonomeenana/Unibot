from PIL import Image
import os

def rename_and_convert(file_path):
    # 打开图片文件
    with Image.open(file_path) as img:
        # 创建新文件名和路径
        new_file_name = file_path.replace(' ', '').replace('(', '').replace(')', '')
        new_file_path = os.path.splitext(new_file_name)[0] + '.jpg'
        
        # 转换图片格式到JPEG
        img.convert('RGB').save(new_file_path, 'JPEG')
        
        # 删除源文件
        os.remove(file_path)

def main():
    for i in range(1, 13):  # 从 1 到 12
        file_name = f"sr ({i}).PNG"
        if os.path.exists(file_name):
            rename_and_convert(file_name)
        else:
            print(f"文件 {file_name} 不存在")

if __name__ == "__main__":
    main()