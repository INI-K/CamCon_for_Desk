#!/usr/bin/env python3
"""
Universal Camera Manager GUI
GUI tool for Nikon authentication and gphoto2 integration
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import socket
import struct
import queue
import os
import sys
from datetime import datetime

# 기존 모듈 import
from nikon_ptp_client import PTPIPClient


class CameraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("범용 카메라 관리자")
        self.root.geometry("800x600")

        # 메시지 큐 (스레드 간 통신용)
        self.message_queue = queue.Queue()

        # 상태 변수
        self.camera_ip = tk.StringVar(value="192.168.147.75")
        self.camera_type = tk.StringVar(value="감지되지 않음")
        self.connection_status = tk.StringVar(value="연결되지 않음")

        # 니콘 연결 유지용 클라이언트
        self.nikon_client = None
        self.nikon_authenticated = False

        self.setup_gui()
        self.start_message_processor()

    def setup_gui(self):
        """GUI 컴포넌트 설정"""

        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 카메라 연결 섹션
        connection_frame = ttk.LabelFrame(main_frame, text="카메라 연결", padding="10")
        connection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(connection_frame, text="카메라 IP:").grid(row=0, column=0, sticky=tk.W)
        ip_entry = ttk.Entry(connection_frame, textvariable=self.camera_ip, width=20)
        ip_entry.grid(row=0, column=1, padx=(5, 10))

        ttk.Button(connection_frame, text="카메라 감지",
                   command=self.detect_camera).grid(row=0, column=2, padx=5)

        # 상태 표시
        status_frame = ttk.Frame(connection_frame)
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Label(status_frame, text="카메라 타입:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.camera_type,
                  foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=(5, 20))

        ttk.Label(status_frame, text="연결 상태:").grid(row=0, column=2, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.connection_status,
                  foreground="green").grid(row=0, column=3, sticky=tk.W, padx=(5, 0))

        # 카메라 제어 섹션
        control_frame = ttk.LabelFrame(main_frame, text="카메라 제어", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(control_frame, text=" 사진 촬영",
                   command=self.capture_image, width=15).grid(row=0, column=0, pady=2)
        ttk.Button(control_frame, text=" 파일 목록",
                   command=self.list_files, width=15).grid(row=1, column=0, pady=2)
        ttk.Button(control_frame, text=" 파일 다운로드",
                   command=self.download_files, width=15).grid(row=2, column=0, pady=2)
        ttk.Button(control_frame, text=" 카메라 설정",
                   command=self.camera_config, width=15).grid(row=3, column=0, pady=2)

        # 고급 제어 섹션
        advanced_frame = ttk.LabelFrame(main_frame, text="고급 제어", padding="10")
        advanced_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), padx=(5, 0))

        ttk.Button(advanced_frame, text=" 니콘 재인증",
                   command=self.reauthenticate_nikon, width=15).grid(row=0, column=0, pady=2)
        ttk.Button(advanced_frame, text=" 자동 감지",
                   command=self.auto_detect, width=15).grid(row=1, column=0, pady=2)
        ttk.Button(advanced_frame, text=" 작업 폴더 열기",
                   command=self.open_work_folder, width=15).grid(row=2, column=0, pady=2)
        ttk.Button(advanced_frame, text=" 로그 지우기",
                   command=self.clear_log, width=15).grid(row=3, column=0, pady=2)

        # 로그 섹션
        log_frame = ttk.LabelFrame(main_frame, text="작업 로그", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log("🎉 범용 카메라 관리자 시작됨")
        self.log("📝 카메라 IP를 입력하고 '카메라 감지' 버튼을 클릭하세요")

    def log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.message_queue.put(('log', log_message))

    def start_message_processor(self):
        """메시지 큐 처리 시작"""

        def process_messages():
            try:
                while True:
                    msg_type, content = self.message_queue.get_nowait()
                    if msg_type == 'log':
                        self.log_text.insert(tk.END, content)
                        self.log_text.see(tk.END)
            except queue.Empty:
                pass
            finally:
                self.root.after(100, process_messages)

        process_messages()

    def run_in_thread(self, func, *args):
        """백그라운드 스레드에서 함수 실행"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()

    def detect_nikon_camera(self, camera_ip):
        """니콘 카메라 감지"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((camera_ip, 15740))

            client_guid = b'test12345678test'
            name_utf16 = "CameraGUI\0".encode('utf-16le')
            packet_length = 8 + 16 + len(name_utf16)

            packet = struct.pack('<II', packet_length, 1)
            packet += client_guid + name_utf16

            sock.send(packet)
            response = sock.recv(1024)
            sock.close()

            if len(response) >= 8:
                length, packet_type = struct.unpack('<II', response[:8])
                if packet_type == 2:
                    return True

        except Exception:
            pass

        return False

    def authenticate_nikon(self, camera_ip):
        """니콘 카메라 인증 및 연결 유지"""
        self.log(" 니콘 카메라 인증 시작...")

        # 기존 연결이 있다면 정리
        if self.nikon_client:
            try:
                self.nikon_client.disconnect()
            except:
                pass
            self.nikon_client = None
            self.nikon_authenticated = False

        try:
            # Phase 1: 승인 요청
            temp_client = PTPIPClient(camera_ip)

            if not temp_client.connect():
                self.log(" 연결 실패")
                return False

            device_info = temp_client.get_device_info()
            if not device_info:
                self.log(" 장치 정보 가져오기 실패")
                return False

            if not temp_client.open_session():
                self.log(" 세션 열기 실패")
                return False

            response_code, _ = temp_client._send_ptp_command(0x952b)
            if response_code != temp_client.PTP_RC_OK:
                self.log(" 0x952b 실패")
                return False

            response_code, _ = temp_client._send_ptp_command_935a()
            if response_code != temp_client.PTP_RC_OK:
                self.log(" 0x935a 승인 실패")
                return False

            self.log(" Phase 1 완료")
            temp_client.disconnect()

            # Phase 2: 인증된 연결 설정 및 유지
            import time
            time.sleep(3)

            self.nikon_client = PTPIPClient(camera_ip)

            if not self.nikon_client.connect():
                self.log(" 인증된 연결 실패")
                return False

            device_info = self.nikon_client.get_device_info()
            if not device_info:
                self.log(" 인증된 장치 정보 실패")
                return False

            if device_info.get('supports_944c'):
                self.log(" 니콘 인증 완료!")
                if self.nikon_client.open_session():
                    self.log(" 인증된 세션 열기 성공")
                    # 연결을 유지한 채로 두기
                    self.nikon_authenticated = True
                    return True
                else:
                    self.log(" 인증된 세션 열기 실패")
                    return False
            else:
                self.log(" 인증 실패 - 고급 기능 비활성화")
                return False

        except Exception as e:
            self.log(f" 인증 중 오류: {e}")
            return False

    def run_gphoto2(self, args):
        """gphoto2 명령 실행"""
        try:
            # 니콘 카메라인 경우 연결 상태 확인
            if self.camera_type.get() == "니콘 카메라":
                if not self.nikon_authenticated or not self.nikon_client:
                    self.log(" 니콘 재인증 필요...")
                    if not self.authenticate_nikon(self.camera_ip.get()):
                        self.log(" 니콘 인증 실패 - gphoto2 사용 불가")
                        return False

                # 니콘 연결을 일시적으로 해제하여 gphoto2가 사용할 수 있게 함
                if self.nikon_client:
                    self.log(" gphoto2 사용을 위해 니콘 연결 일시 해제...")
                    self.nikon_client.disconnect()
                    self.nikon_client = None
                    self.nikon_authenticated = False

                    # gphoto2가 접근할 수 있도록 잠깐 대기
                    import time
                    time.sleep(1)

            cmd = ['gphoto2'] + args
            self.log(f" 실행: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                self.log(" gphoto2 명령 성공")
                if result.stdout.strip():
                    # 출력을 로그에 추가
                    for line in result.stdout.strip().split('\n'):
                        self.log(f" {line}")
                return True
            else:
                self.log(f" gphoto2 실패: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            self.log(" gphoto2 명령 타임아웃")
            return False
        except Exception as e:
            self.log(f" gphoto2 오류: {e}")
            return False

    def cleanup_connections(self):
        """연결 정리"""
        if self.nikon_client:
            try:
                self.log(" 니콘 연결 정리 중...")
                self.nikon_client.disconnect()
            except:
                pass
            finally:
                self.nikon_client = None
                self.nikon_authenticated = False

    # 버튼 이벤트 핸들러들
    def detect_camera(self):
        """카메라 감지"""

        def _detect():
            camera_ip = self.camera_ip.get()
            self.log(f" 카메라 감지 시작: {camera_ip}")

            if self.detect_nikon_camera(camera_ip):
                self.camera_type.set("니콘 카메라")
                self.log(" 니콘 카메라 감지됨")

                if self.authenticate_nikon(camera_ip):
                    self.connection_status.set("인증 완료")
                    self.log(" 인증 완료 - 모든 기능 사용 가능")
                else:
                    self.connection_status.set("인증 실패")
            else:
                self.camera_type.set("일반 카메라")
                self.connection_status.set("연결 가능")
                self.log(" 일반 카메라 감지됨")

            # gphoto2로 확인
            self.run_gphoto2(['--auto-detect'])

        self.run_in_thread(_detect)

    def capture_image(self):
        """사진 촬영"""

        def _capture():
            camera_ip = self.camera_ip.get()

            if self.camera_type.get() == "니콘 카메라":
                if not self.nikon_authenticated or not self.nikon_client:
                    self.log(" 니콘 재인증 필요...")
                    if self.authenticate_nikon(camera_ip):
                        self.nikon_authenticated = True
                    else:
                        self.log(" 니콘 인증 실패 - gphoto2 사용 불가")
                        return

            self.log(" 사진 촬영 시작...")
            if self.run_gphoto2(['--capture-image']):
                self.log(" 사진 촬영 완료!")

        self.run_in_thread(_capture)

    def list_files(self):
        """파일 목록"""

        def _list():
            camera_ip = self.camera_ip.get()

            if self.camera_type.get() == "니콘 카메라":
                if not self.nikon_authenticated or not self.nikon_client:
                    self.log(" 니콘 재인증 필요...")
                    if self.authenticate_nikon(camera_ip):
                        self.nikon_authenticated = True
                    else:
                        self.log(" 니콘 인증 실패 - gphoto2 사용 불가")
                        return

            self.log(" 파일 목록 조회 중...")
            self.run_gphoto2(['--list-files'])

        self.run_in_thread(_list)

    def download_files(self):
        """파일 다운로드"""

        def _download():
            # 다운로드 폴더 선택
            download_dir = filedialog.askdirectory(title="다운로드 폴더 선택")
            if not download_dir:
                return

            camera_ip = self.camera_ip.get()

            if self.camera_type.get() == "니콘 카메라":
                if not self.nikon_authenticated or not self.nikon_client:
                    self.log(" 니콘 재인증 필요...")
                    if self.authenticate_nikon(camera_ip):
                        self.nikon_authenticated = True
                    else:
                        self.log(" 니콘 인증 실패 - gphoto2 사용 불가")
                        return

            self.log(f" 파일 다운로드 시작: {download_dir}")

            # 작업 디렉토리 변경
            original_dir = os.getcwd()
            os.chdir(download_dir)

            try:
                if self.run_gphoto2(['--get-all-files']):
                    self.log(" 파일 다운로드 완료!")
            finally:
                os.chdir(original_dir)

        self.run_in_thread(_download)

    def camera_config(self):
        """카메라 설정"""

        def _config():
            camera_ip = self.camera_ip.get()

            if self.camera_type.get() == "니콘 카메라":
                if not self.nikon_authenticated or not self.nikon_client:
                    self.log(" 니콘 재인증 필요...")
                    if self.authenticate_nikon(camera_ip):
                        self.nikon_authenticated = True
                    else:
                        self.log(" 니콘 인증 실패 - gphoto2 사용 불가")
                        return

            self.log(" 카메라 설정 조회 중...")
            self.run_gphoto2(['--list-config'])

        self.run_in_thread(_config)

    def reauthenticate_nikon(self):
        """니콘 재인증"""

        def _reauth():
            camera_ip = self.camera_ip.get()
            self.log(" 니콘 카메라 재인증 시작...")

            if self.authenticate_nikon(camera_ip):
                self.connection_status.set("재인증 완료")
                self.log(" 재인증 성공!")
            else:
                self.connection_status.set("재인증 실패")

        self.run_in_thread(_reauth)

    def auto_detect(self):
        """자동 감지"""

        def _auto():
            self.log(" 카메라 자동 감지 중...")
            self.run_gphoto2(['--auto-detect'])

        self.run_in_thread(_auto)

    def open_work_folder(self):
        """작업 폴더 열기"""
        work_dir = os.getcwd()
        if sys.platform == "darwin":  # macOS
            subprocess.run(['open', work_dir])
        elif sys.platform == "win32":  # Windows
            subprocess.run(['explorer', work_dir])
        else:  # Linux
            subprocess.run(['xdg-open', work_dir])
        self.log(f" 작업 폴더 열기: {work_dir}")

    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)
        self.log(" 로그가 지워졌습니다")


def main():
    root = tk.Tk()
    app = CameraGUI(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("GUI 종료")
        app.cleanup_connections()


if __name__ == "__main__":
    main()
