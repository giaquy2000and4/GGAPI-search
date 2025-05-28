import requests
import os
from PIL import Image
from io import BytesIO

# --- Cấu hình ---
API_KEY = 'AIzaSyBYUEQzOl5wF5wObQaN0DDn6E7KDZHYhlc'
CX = '72be8b4014fac4e40'
SAVE_FOLDER = "images"
LOG_FILE = "downloaded_log.txt"

# --- Đọc log ảnh đã tải ---
def load_downloaded_urls():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

# --- Ghi URL mới vào log ---
def save_url_to_log(url):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(url + '\n')

# --- Tìm ảnh từ Google ---
def search_image_on_google(query, num_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": CX,
        "key": API_KEY,
        "searchType": "image",
        "num": num_results,
        "imgSize": "xlarge"
    }
    response = requests.get(url, params=params)
    results = response.json()
    return [item["link"] for item in results.get("items", [])]

# --- Tải và lưu ảnh nếu hợp lệ ---
def download_and_convert_to_png(url, save_folder, filename_index):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=10)

        if 'image' not in response.headers.get("Content-Type", ""):
            print("⚠️ Không phải ảnh hợp lệ, bỏ qua.")
            return False

        image = Image.open(BytesIO(response.content))
        width, height = image.size
        aspect_ratio = width / height

        if width < height or aspect_ratio < 1.3:
            print(f"⛔ Ảnh không đúng tỉ lệ ngang (w={width}, h={height}, tỉ lệ={aspect_ratio:.2f}), bỏ qua.")
            return False

        os.makedirs(save_folder, exist_ok=True)
        filename = f"{filename_index:03d}.png"
        path = os.path.join(save_folder, filename)
        image.save(path, "PNG")
        print(f"✅ Đã lưu ảnh: {path}")
        return True

    except Exception as e:
        print(f"❌ Lỗi xử lý ảnh: {e}")
        return False

# --- Đọc danh sách từ khóa ---
def load_keywords(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

# --- Đếm số ảnh đã có ---
def count_existing_images(folder):
    if not os.path.exists(folder):
        return 0
    return len([f for f in os.listdir(folder) if f.endswith(".png")])

# --- Xử lý từng từ khóa ---
def process_keywords(file_path):
    keywords = load_keywords(file_path)
    downloaded_urls = load_downloaded_urls()
    index = count_existing_images(SAVE_FOLDER) + 1

    for keyword in keywords:
        print(f"\n🔍 Tìm ảnh cho: {keyword}")
        image_urls = search_image_on_google(keyword)
        success = False

        for url in image_urls:
            if url in downloaded_urls:
                print("⏭️ Đã tải ảnh này trước đó, bỏ qua.")
                continue
            if download_and_convert_to_png(url, SAVE_FOLDER, index):
                save_url_to_log(url)
                index += 1
                success = True
                break

        if not success:
            print(f"⚠️ Không tìm được ảnh phù hợp cho: {keyword}")

# --- Chạy chương trình ---
if __name__ == "__main__":
    process_keywords("keywords.txt")
