#!/usr/bin/env python3
"""
Nikon Camera Authenticator for gphoto2 Integration
Performs 0x935a authentication and disconnects for gphoto2 usage
"""

import sys
import time
import logging
from nikon_ptp_client import PTPIPClient

# 간단한 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def authenticate_nikon(camera_ip):
    """니콘 카메라 인증만 수행하고 즉시 연결 해제"""
    logger.info(f"니콘 카메라 인증 시작: {camera_ip}")

    # Phase 1: 초기 연결 및 승인 요청
    logger.info("Phase 1: 초기 연결 및 0x935a 승인 요청")
    client = PTPIPClient(camera_ip)

    try:
        # 1-5단계: 기존 로직과 동일
        if not client.connect():
            logger.error("연결 실패")
            return False

        device_info = client.get_device_info()
        if not device_info:
            logger.error("장치 정보 가져오기 실패")
            return False

        if not client.open_session():
            logger.error("세션 열기 실패")
            return False

        response_code, _ = client._send_ptp_command(0x952b)
        if response_code != client.PTP_RC_OK:
            logger.error("0x952b 실패")
            return False

        response_code, _ = client._send_ptp_command_935a()
        if response_code != client.PTP_RC_OK:
            logger.error("0x935a 승인 실패")
            return False

        logger.info("✅ Phase 1 완료 - 연결 승인 성공")

    except Exception as e:
        logger.error(f"Phase 1 오류: {e}")
        return False
    finally:
        client.disconnect()

    # 카메라 내부 처리 대기
    logger.info("카메라 상태 변경 대기 중... (3초)")
    time.sleep(3)

    # Phase 2: 인증된 연결 확인 후 즉시 해제
    logger.info("Phase 2: 인증 상태 확인")
    auth_client = PTPIPClient(camera_ip)

    try:
        if not auth_client.connect():
            logger.error("인증된 연결 실패")
            return False

        device_info = auth_client.get_device_info()
        if not device_info:
            logger.error("인증된 장치 정보 가져오기 실패")
            return False

        # 인증 성공 확인
        if device_info.get('supports_944c'):
            logger.info("✅ 인증 완료 - 모든 기능 활성화됨")

            # 빠른 세션 열기/닫기로 연결 상태 확정
            if auth_client.open_session():
                logger.info("✅ 인증된 세션 확인")
                auth_client.close_session()

            return True
        else:
            logger.error("인증 실패 - 고급 기능 비활성화")
            return False

    except Exception as e:
        logger.error(f"Phase 2 오류: {e}")
        return False
    finally:
        # 중요: gphoto2 사용을 위해 즉시 연결 해제
        auth_client.disconnect()
        logger.info("✅ 인증 완료 - gphoto2 사용 가능")


def main():
    if len(sys.argv) != 2:
        print("사용법: python3 nikon_authenticator.py <카메라_IP>")
        print("예시: python3 nikon_authenticator.py 192.168.147.75")
        sys.exit(1)

    camera_ip = sys.argv[1]

    logger.info("=" * 60)
    logger.info("니콘 카메라 인증기 - gphoto2 통합용")
    logger.info("=" * 60)

    success = authenticate_nikon(camera_ip)

    if success:
        logger.info("🎉 인증 성공! 이제 gphoto2를 사용할 수 있습니다.")
        logger.info("예시: gphoto2 --auto-detect")
        logger.info("예시: gphoto2 --list-files")
        logger.info("예시: gphoto2 --capture-image")
        sys.exit(0)
    else:
        logger.error("❌ 인증 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
