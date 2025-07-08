#!/usr/bin/env python3
"""
Universal Camera Manager
Handles Nikon authentication and integrates with gphoto2 for all camera brands
"""

import subprocess
import sys
import socket
import struct
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_nikon_camera(camera_ip):
    """니콘 카메라인지 PTP 연결로 확인"""
    try:
        # PTP/IP 포트에 연결 시도
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((camera_ip, 15740))

        # 간단한 Init Command Request 전송
        client_guid = b'test12345678test'  # 16바이트
        name_utf16 = "Test\0".encode('utf-16le')
        packet_length = 8 + 16 + len(name_utf16)

        packet = struct.pack('<II', packet_length, 1)  # length, INIT_COMMAND_REQUEST
        packet += client_guid + name_utf16

        sock.send(packet)
        response = sock.recv(1024)
        sock.close()

        if len(response) >= 8:
            length, packet_type = struct.unpack('<II', response[:8])
            if packet_type == 2:  # INIT_COMMAND_ACK
                logger.info("✅ 니콘 카메라 감지됨")
                return True

    except Exception as e:
        logger.debug(f"PTP 연결 실패 (정상): {e}")

    return False


def authenticate_nikon(camera_ip):
    """니콘 카메라 인증 수행"""
    logger.info("니콘 카메라 인증 중...")

    try:
        result = subprocess.run([
            'python3', 'nikon_authenticator.py', camera_ip
        ], capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            logger.info("✅ 니콘 인증 성공")
            return True
        else:
            logger.error(f"❌ 니콘 인증 실패: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("❌ 니콘 인증 타임아웃")
        return False
    except Exception as e:
        logger.error(f"❌ 니콘 인증 오류: {e}")
        return False


def run_gphoto2_command(command_args):
    """gphoto2 명령 실행"""
    try:
        cmd = ['gphoto2'] + command_args
        logger.info(f"gphoto2 실행: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ gphoto2 명령 성공")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            logger.error(f"❌ gphoto2 명령 실패: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ gphoto2 실행 오류: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("범용 카메라 관리자")
        print("")
        print("사용법:")
        print("  python3 camera_manager.py detect <IP>           # 카메라 감지")
        print("  python3 camera_manager.py capture <IP>          # 사진 촬영")
        print("  python3 camera_manager.py list <IP>             # 파일 목록")
        print("  python3 camera_manager.py download <IP>         # 파일 다운로드")
        print("  python3 camera_manager.py gphoto2 <IP> [args]   # 직접 gphoto2 명령")
        print("")
        print("예시:")
        print("  python3 camera_manager.py detect 192.168.147.75")
        print("  python3 camera_manager.py capture 192.168.147.75")
        print("  python3 camera_manager.py gphoto2 192.168.147.75 --list-files")
        sys.exit(1)

    command = sys.argv[1]

    if command == "detect":
        if len(sys.argv) != 3:
            print("사용법: python3 camera_manager.py detect <IP>")
            sys.exit(1)

        camera_ip = sys.argv[2]

        logger.info(f"카메라 감지 중: {camera_ip}")

        if detect_nikon_camera(camera_ip):
            logger.info("📷 니콘 카메라 감지 - 인증 필요")
            if authenticate_nikon(camera_ip):
                logger.info("🎉 인증 완료 - gphoto2 사용 가능")
            else:
                logger.error("❌ 인증 실패")
                sys.exit(1)
        else:
            logger.info("📷 일반 카메라 감지 - gphoto2 직접 사용 가능")

        # gphoto2로 카메라 확인
        logger.info("gphoto2로 카메라 상태 확인...")
        run_gphoto2_command(['--auto-detect'])

    elif command in ["capture", "list", "download"]:
        if len(sys.argv) != 3:
            print(f"사용법: python3 camera_manager.py {command} <IP>")
            sys.exit(1)

        camera_ip = sys.argv[2]

        # 니콘 카메라인지 확인하고 필요시 인증
        if detect_nikon_camera(camera_ip):
            logger.info("니콘 카메라 - 인증 수행")
            if not authenticate_nikon(camera_ip):
                logger.error("인증 실패")
                sys.exit(1)

        # 작업 수행
        if command == "capture":
            run_gphoto2_command(['--capture-image'])
        elif command == "list":
            run_gphoto2_command(['--list-files'])
        elif command == "download":
            run_gphoto2_command(['--get-all-files'])

    elif command == "gphoto2":
        if len(sys.argv) < 4:
            print("사용법: python3 camera_manager.py gphoto2 <IP> [gphoto2_args...]")
            sys.exit(1)

        camera_ip = sys.argv[2]
        gphoto2_args = sys.argv[3:]

        # 니콘 카메라인지 확인하고 필요시 인증
        if detect_nikon_camera(camera_ip):
            logger.info("니콘 카메라 - 인증 수행")
            if not authenticate_nikon(camera_ip):
                logger.error("인증 실패")
                sys.exit(1)

        # gphoto2 명령 실행
        run_gphoto2_command(gphoto2_args)

    else:
        print(f"알 수 없는 명령: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
