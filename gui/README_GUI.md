# Tool AF — Giao diện Desktop (GUI)

App desktop Python + CustomTkinter cho Tool AF: quản lý 16 page (mục tiêu 50
page), gán kênh Douyin, edit video bằng FFmpeg, upload lên Facebook qua Graph
API, kèm caption/comment gắn link Shopee Affiliate.

Chạy trên **Windows 10/11**, bấm đúp file `.exe` là mở. Code gốc (3 script CLI)
giữ nguyên hành vi — GUI chỉ là lớp bọc mỏng bên trên.

## Chạy nhanh (trên máy Han)

**Cách 1 — file .exe (khuyến nghị):**

```bat
cd gui
build.bat
```

`build.bat` làm 4 bước: kiểm tra Python → tạo venv `.venv-gui` → `pip install
-r requirements.txt` → PyInstaller `--onefile --noconsole` ra
`gui\dist\ToolAF.exe`. Copy `ToolAF.exe` vào thư mục Tool AF
(vd `D:\Tool AF\`, cùng chỗ với `Uploadvideo_multipage.py`) rồi bấm đúp để chạy.

**Cách 2 — chạy bằng Python (không cần build):**

```bat
cd gui
python -m venv .venv-gui
.venv-gui\Scripts\activate
pip install -r requirements.txt
python app.py
```

> Lưu ý: `.exe` Windows **không build được trên VM Linux** — Han chạy
> `build.bat` trên máy mình để ra file `.exe`.

## 12 màn hình

| # | Màn hình | Làm gì |
|---|----------|--------|
| 1 | Dashboard | 6 thẻ số liệu (Page / Đã gắn / Đang đợi / Video pool / Đã edit / Đã đăng hôm nay) + bảng page có **tìm kiếm + lọc trạng thái** (đã gắn / WAITING / lỗi token) |
| 2 | Page | Quét Page từ User Token, kiểm tra token từng page (còn sống/chết), làm mới token, gán tag ngách |
| 3 | Link Pool | Xem trước gán kênh (**dry-run, không ghi file**) / Áp dụng gán / Gán tay / Gỡ gán — STRICT 1-1, FIFO |
| 4 | Kênh nguồn | Thêm/xóa kênh Douyin trong pool, xem kênh nào chưa gán |
| 5 | Xử lý video | Pipeline FFmpeg: chỉnh thông số (tốc độ, crop, contrast, noise...), **dao động nhẹ mỗi video** (tắt mặc định), xem trước video đã edit, chọn tất cả/1 page |
| 6 | Upload | Chọn 1 page hoặc tất cả, xáo trộn, nghỉ giữa video (10s), chờ trước khi comment (15s), simple/resumable, nhập tay 1 file khi edited/ trống, **Tiếp tục đợt dở** |
| 7 | Caption & Comment | Sửa kho caption chung (47 dòng) / comment chung (100 dòng), xem **link Shopee nào đang xoay vòng** (hiện 3 link) + thêm link mới, caption riêng từng page |
| 8 | Nhạc nền | Thêm/xóa file nhạc trong `bgm/`, bật/tắt trộn nhạc, xem mức trộn (0.18) |
| 9 | Lịch sử | Nhật ký edit/upload/sự kiện an toàn (file JSON local), tóm tắt từng đợt chạy |
| 10 | Dữ liệu cũ | Liệt kê `Non_edit/` + `pool_done.txt` còn sót (HANZ, TND) — chuyển video thô vào pool hoặc xóa, **luôn hỏi xác nhận** |
| 11 | Hẹn giờ | Chạy tự động mỗi ngày theo giờ hẹn (khi app đang mở): edit xoay vòng rồi upload |
| 12 | Cài đặt | Tool root, pool root, User Token, **FFmpeg đang dùng (nguồn + phiên bản)**, các công tắc an toàn |

## 7 mục bổ sung (lượt rà soát cuối)

1. **Dừng khi gặp checkpoint / rate-limit (mặc định BẬT):** tool gốc chỉ in
   lỗi rồi chạy tiếp. GUI tự dừng toàn bộ đợt chạy khi Facebook trả checkpoint,
   khóa tài khoản, 429 hoặc token hết hạn; hiện **banner đỏ** ghi rõ lý do +
   page/video đang chạy dở; ghi sự kiện vào Lịch sử; **không tự chạy lại** —
   chỉ chạy tiếp khi Han bấm tay.
2. **Giới hạn số video/ngày (mặc định BẬT, 1 video/page/ngày):** đúng nhịp vận
   hành của Han. Dashboard hiện "đã đăng hôm nay x/1" từng page. Khi API trả
   429 thì đặt **backoff** (mặc định 15 phút) — trong thời gian backoff, chạy
   tay vẫn được nhưng app cảnh báo.
3. **Caption theo ngách từng page (mặc định TẮT = dùng chung như cũ):** page
   nào có file `captions_gui.txt` riêng thì dùng kho đó; không có thì dùng kho
   theo tag ngách (`gui_data/caption_pools/<tag>.txt`); chưa có nữa thì về kho
   chung.
4. **Ngẫu nhiên nhẹ thông số xử lý (mặc định TẮT):** mọi video đang qua đúng 1
   công thức cố định nên dễ bị bắt mẫu. Khi bật, mỗi video lấy mẫu ngẫu nhiên
   trong khoảng Han chỉnh được (vd tốc độ 1.03–1.06, contrast 1.02–1.06).
5. **Dọn dữ liệu cũ:** xem mục 10 ở trên.
6. **Tìm kiếm / lọc page:** ô tìm kiếm + lọc theo trạng thái trên Dashboard và
   màn Page (chuẩn bị lên 50 page).
7. **Hiển thị FFmpeg đang dùng:** trong Cài đặt — nguồn (FFMPEG_BIN /
   imageio-ffmpeg / PATH / chỉ tay) + phiên bản + cho phép chỉ đường dẫn tay.

## An toàn (bắt buộc, đã cài trong code)

- **Không gọi `retrofit_all_pages()` từ GUI** (hàm này xóa `Non_edit/` và
  `videos/` không hỏi). GUI chỉ tự tạo `edited/` khi thiếu, không xóa gì mà
  không có xác nhận.
- **Mặc định KHÔNG xóa video gốc sau khi edit** (khác CLI gốc). Chống đăng
  trùng bằng run-log (lưu hash nguồn + video ID Facebook đã đăng). Có tùy chọn
  bật xóa nguồn trong Cài đặt/Xử lý video, mặc định tắt.
- **Token không bao giờ lên git:** `gui_config.json` (chứa token) và
  `gui_runlog.json` đều nằm trong `.gitignore`. Token cũng đồng bộ sang
  `page_tok.txt` (đã gitignore từ trước) để CLI gốc dùng được.
- **Chống trùng 2 lớp:** hash video gốc đã edit + hash file đã đăng (kèm ID
  Facebook). Chạy lỗi giữa chừng thì bấm "Tiếp tục đợt dở" thay vì chạy lại
  từ đầu.
- Tên thư mục tiếng Việt: mọi thao tác file dùng Python (`pathlib`), không
  dùng shell glob.

## Bảng màu & chuẩn thẩm mỹ (dùng xuyên suốt app)

| Vai trò | Màu | Ghi chú |
|---|---|---|
| Nền chính | `#121417` | tối |
| Nền thẻ (card) | `#1B1E23` | hơi sáng hơn nền chính |
| Nền ô nhập | `#23272E` | |
| Sidebar | `#0E1013` | đậm nhất |
| Chữ chính | `#F2F3F5` | trắng |
| Chữ phụ | `#9AA3AF` | xám nhạt |
| **Accent (duy nhất)** | `#2E86FF` | nút chính / link |
| Xanh lá = OK/đã gắn | `#2ECC71` | |
| Vàng = đang đợi | `#F5B301` | |
| Đỏ = lỗi/hết hạn/nguy hiểm | `#E5484D` | nút xóa cũng dùng màu này |

- Font: **Segoe UI** (Windows), tiêu đề 16–18 bold, nội dung 12–13; log
  console dùng **Consolas** monospace, nền tối.
- Sidebar trái cố định: logo "Tool AF" + menu 12 màn hình + trạng thái token
  ở dưới. Nội dung bên phải. Không dùng tab mặc định.
- Dashboard dạng thẻ bo góc 10px, số liệu lớn + nhãn nhỏ, padding chuẩn
  14px mọi màn hình. Bảng: header đậm, hàng xen kẽ 2 tông nền, trạng thái
  dạng "pill" bo tròn có màu.
- Thanh tiến độ thật + % + dòng trạng thái (đang làm gì, video thứ mấy) ở
  console dưới; nút **■ Dừng** khẩn cấp luôn hiện khi có tác vụ chạy.
- Mọi form nhập liệu có nhãn rõ + placeholder ví dụ + nút duyệt thư mục/file.

## Cấu trúc code

```text
gui/
  app.py                 # cửa sổ chính: sidebar + banner đỏ + console + scheduler
  theme.py               # bảng màu + font + pill trạng thái (1 chỗ duy nhất)
  workers.py             # chạy tác vụ dài trên thread riêng + nút Dừng
  requirements.txt       # customtkinter, requests, imageio-ffmpeg, PyInstaller
  build.bat              # build ToolAF.exe trên Windows
  core/                  # logic thuần (test được headless, không cần màn hình)
    config.py            # gui_config.json (local, gitignore)
    store.py             # đọc/ghi pages/, pool, captions, comments, bgm, legacy
    runlog.py            # gui_runlog.json: chống trùng, tiếp tục, giới hạn/ngày
    safety.py            # phân loại lỗi FB: checkpoint / rate-limit / token
    pipeline.py          # dao động nhẹ (jitter) thông số xử lý
    ffmpeg.py            # tìm FFmpeg + phiên bản
    scheduler.py         # giờ hẹn chạy tự động
  adapters/              # lớp mỏng bọc 3 script gốc (không đổi logic gốc)
    pool_adapter.py      # link_pool.py
    processing_adapter.py# video_processing/Processing.py
    upload_adapter.py    # Uploadvideo_multipage.py (+ điều phối đợt upload)
  views/                 # 12 màn hình (mỗi màn: build_model thuần + widget)
    common.py            # card / nút / pill / bảng dùng chung theo theme
    dashboard.py  pages_view.py  pool_view.py  channels_view.py
    processing_view.py  upload_view.py  captions_view.py  bgm_view.py
    history_view.py  legacy_view.py  scheduler_view.py  settings_view.py
  tests/                 # pytest, chạy headless (trừ test_app.py cần Xvfb)
```

## Test

```bash
# Trên VM Linux (cần venv có pytest + customtkinter + requests):
python -m pytest gui/tests -q
# Test cửa sổ GUI thật (cần màn hình ảo):
xvfb-run -a python -m pytest gui/tests -q
```

Mỗi module có test riêng (config, safety, pipeline, ffmpeg, scheduler, store,
runlog, theme, 3 adapter, workers, 12 view-model, app smoke test, build.bat).
Đường chạy demo-critical đã kiểm chứng: app khởi động + chuyển 12 màn hình,
Dashboard load 16 page từ dữ liệu thật trong repo, dry-run link pool không
ghi file, run-log ghi/đọc đúng, config lưu/load đúng, build.bat đủ 4 bước.

## Những thứ GUI KHÔNG làm

- **Không có màn analytics / hoa hồng:** tool gốc không có dữ liệu đó nên
  GUI không bịa số liệu. Muốn xem hiệu quả thì xem Facebook Insights /
  Shopee Affiliate.
- Không xử lý checkpoint thay Han — chỉ dừng lại và báo rõ để Han tự xử lý.
- Upload resumable của tool gốc gửi toàn bộ file trong 1 request (không chia
  chunk) — GUI giữ nguyên hành vi này, không sửa.

## File local (không commit)

- `gui_config.json` — cấu hình + token (thư mục tool).
- `gui_runlog.json` — nhật ký chạy (thư mục tool).
- `gui_data/caption_pools/<tag>.txt` — kho caption theo tag ngách.
- `pages/<folder>/captions_gui.txt` — kho caption riêng từng page.
- `pages/<folder>/niche.txt` — tag ngách từng page.
