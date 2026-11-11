# Tool AF — Hệ thống đăng video tự động lên nhiều Facebook Page

Hệ thống Python chạy trên Windows, vận hành nhiều Facebook Page cùng lúc theo
mô hình re-up video: lấy video nguồn từ Douyin, xử lý chống trùng lặp bằng
FFmpeg rồi đăng hàng loạt qua Facebook Graph API, kèm caption ngẫu nhiên và
bình luận gắn link Shopee Affiliate.

## Tính năng

- **Quản lý Page** (`Uploadvideo_multipage.py`): quét tất cả Page từ User Token
  (`GET /me/accounts`, Graph API v21.0), tự tạo thư mục cho từng page, làm mới
  token page mỗi lần chạy.
- **Upload video**: 2 chế độ — simple upload và resumable 3 bước (tự đổi khi
  lỗi), caption ngẫu nhiên từ `captions.txt`, tự bình luận link Affiliate sau
  15 giây, xáo trộn thứ tự video, nghỉ 10 giây giữa các video.
- **Link Pool** (`link_pool.py`): gán STRICT 1-1 — 1 page = 1 kênh Douyin duy
  nhất, tự gán kênh trống cho page đang đợi theo FIFO, xuất bảng `pool_map.txt`,
  hỗ trợ `--dry-run`.
- **Xử lý video** (`video_processing/Processing.py`): pipeline FFmpeg chống
  trùng lặp — cắt đầu/cuối, tăng tốc 1,045×, lật ngang, zoom/crop, đổi màu nhẹ,
  thêm nhiễu, trộn nhạc nền ngẫu nhiên, xóa metadata, encode H.264/AAC (CRF 20).
  Edit xong xóa video nguồn để chống đăng trùng; mỗi lượt chỉ edit 1 video/page.

## Cấu trúc

```text
Uploadvideo_multipage.py   # upload + quản lý page (menu CLI)
link_pool.py               # gán kênh Douyin cho page (STRICT 1-1)
video_processing/
  Processing.py            # pipeline FFmpeg chống trùng lặp
  bgm/                     # nhạc nền trộn vào video (thêm file .mp3/.wav vào đây)
captions.txt               # kho caption (47 dòng)
comments.txt               # kho comment gắn link Shopee Affiliate (100 dòng)
pool_map.txt               # bảng gán page <-> kênh Douyin
pages/<PageID>_<Ten>/
  info.txt                 # tên + ID page
  source.txt               # kênh Douyin được gán cho page
  pool_done.txt            # (legacy) video đã lấy từ pool
  edited/                  # video đã xử lý, chờ upload
```

## Giao diện Desktop (GUI)

App desktop Python + CustomTkinter trong `gui/` — quản lý page, gán kênh,
edit video, upload, hẹn giờ, chống trùng bằng run-log. Xem hướng dẫn đầy đủ:
**[gui/README_GUI.md](gui/README_GUI.md)**.

```bat
cd gui
build.bat        # ra gui\dist\ToolAF.exe (chạy trên Windows)
```

## Cài đặt

```bash
pip install requests
# cần FFmpeg trong PATH (hoặc đặt biến môi trường FFMPEG_BIN)
```

## Token (KHÔNG commit lên repo)

Tool cần 2 loại token, phải tự tạo file ở máy local — **không có trong repo này**:

- `page_tok.txt` ở thư mục gốc: User Token Facebook (để fetch danh sách Page).
- `pages/<PageID>_<Ten>/token.txt`: Page Token từng page (tool tự ghi khi fetch
  được từ User Token; nếu fetch thất bại mới đọc file này).
- Hoặc đặt biến môi trường `FB_USER_TOKEN` (xem `TOKEN` trong
  `Uploadvideo_multipage.py`).

## Cách chạy

```bash
# 1. Gán kênh Douyin cho các page đang đợi
python link_pool.py

# 2. Edit video từ pool sang edited/ (menu: xem trạng thái / edit 1 page / edit tất cả)
python video_processing/Processing.py

# 3. Upload video đã edit lên Page (menu: 1 page hoặc tất cả page)
python Uploadvideo_multipage.py
```

## Lưu ý

- Repo này chỉ chứa code + cấu hình mẫu. Video, nhạc nền, token và dữ liệu
  tài khoản KHÔNG được đưa lên GitHub (xem `.gitignore`).
- Tool không xử lý checkpoint/rate-limit/token hết hạn của Facebook — cần
  theo dõi thủ công khi chạy số lượng lớn.
- `pages/*/Non_edit/` và `pool_done.txt` là dấu vết workflow cũ (trước
  07/10/2026), code hiện tại không còn dùng.
