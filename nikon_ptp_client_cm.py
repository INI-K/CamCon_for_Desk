# #!/usr/bin/env python3
# """
# Nikon PTP/IP Client with PIN Authentication for STA Mode
# Based on packet analysis of official app communication
# """
#
# import os
# from datetime import datetime
# import socket
# import struct
# import threading
# import time
# import uuid
# import logging
# from typing import Optional, List, Tuple
#
# # 로그 파일 이름 생성 (현재 시간 포함)
# log_filename = f"nikon_ptp_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
#
# # 로거 설정
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
#
# # 포맷터 설정
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#
# # 콘솔 핸들러 (터미널 출력)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)  # 콘솔에도 DEBUG 레벨 출력으로 변경
# console_handler.setFormatter(formatter)
#
# # 파일 핸들러 (파일 저장)
# file_handler = logging.FileHandler(log_filename, encoding='utf-8')
# file_handler.setLevel(logging.DEBUG)  # 파일에는 모든 레벨 저장
# file_handler.setFormatter(formatter)
#
# # 핸들러들을 로거에 추가
# logger.addHandler(console_handler)
# logger.addHandler(file_handler)
#
# # 시작 메시지
# logger.info(f"로그 파일 생성: {log_filename}")
# logger.info("=" * 60)
#
#
# class PTPIPClient:
#     """니콘 카메라와 PTP/IP 프로토콜로 통신하는 클라이언트 클래스"""
#
#     # PTP/IP 패킷 타입 정의
#     PTPIP_INIT_COMMAND_REQUEST = 1  # 명령 채널 초기화 요청
#     PTPIP_INIT_COMMAND_ACK = 2  # 명령 채널 초기화 응답
#     PTPIP_INIT_EVENT_REQUEST = 3  # 이벤트 채널 초기화 요청
#     PTPIP_INIT_EVENT_ACK = 4  # 이벤트 채널 초기화 응답
#     PTPIP_INIT_FAIL = 5  # 초기화 실패
#     PTPIP_CMD_REQUEST = 6  # 명령 요청
#     PTPIP_CMD_RESPONSE = 7  # 명령 응답
#     PTPIP_EVENT = 8  # 이벤트
#     PTPIP_START_DATA_PACKET = 9  # 데이터 패킷 시작
#     PTPIP_DATA_PACKET = 10  # 데이터 패킷
#     PTPIP_CANCEL_TRANSACTION = 11  # 트랜잭션 취소
#     PTPIP_END_DATA_PACKET = 12  # 데이터 패킷 종료
#
#     # PTP 동작 코드 정의 (순서대로 정리)
#     PTP_OC_GetDeviceInfo = 0x1001  # 장치 정보 가져오기
#     PTP_OC_OpenSession = 0x1002  # 세션 열기
#     PTP_OC_CloseSession = 0x1003  # 세션 닫기
#     PTP_OC_GetStorageIDs = 0x1004  # 저장소 ID 가져오기
#     PTP_OC_GetStorageInfo = 0x1005  # 저장소 정보 가져오기
#     PTP_OC_GetNumObjects = 0x1006  # 객체 개수 가져오기
#     PTP_OC_GetObjectHandles = 0x1007  # 객체 핸들 가져오기
#     PTP_OC_GetObjectInfo = 0x1008  # 객체 정보 가져오기
#     PTP_OC_GetObject = 0x1009  # 객체 가져오기
#     PTP_OC_GetThumb = 0x100A  # 썸네일 가져오기
#     PTP_OC_DeleteObject = 0x100B  # 객체 삭제
#     PTP_OC_SendObjectInfo = 0x100C  # 객체 정보 전송
#     PTP_OC_SendObject = 0x100D  # 객체 전송
#     PTP_OC_InitiateCapture = 0x100E  # 촬영 시작
#     PTP_OC_FormatStore = 0x100F  # 저장소 포맷
#     PTP_OC_ResetDevice = 0x1010  # 장치 리셋
#     PTP_OC_SelfTest = 0x1011  # 자가 진단
#     PTP_OC_SetObjectProtection = 0x1012  # 객체 보호 설정
#     PTP_OC_PowerDown = 0x1013  # 전원 끄기
#     PTP_OC_GetDevicePropDesc = 0x1014  # 장치 속성 설명 가져오기
#     PTP_OC_GetDevicePropValue = 0x1015  # 장치 속성 값 가져오기
#     PTP_OC_SetDevicePropValue = 0x1016  # 장치 속성 값 설정
#     PTP_OC_ResetDevicePropValue = 0x1017  # 장치 속성 값 리셋
#     PTP_OC_TerminateOpenCapture = 0x1018  # 열린 촬영 종료
#     PTP_OC_MoveObject = 0x1019  # 객체 이동
#     PTP_OC_CopyObject = 0x101A  # 객체 복사
#     PTP_OC_GetPartialObject = 0x101B  # 부분 객체 가져오기
#     PTP_OC_InitiateOpenCapture = 0x101C  # 열린 촬영 시작
#
#     # 니콘 전용 동작 코드 (순서대로 정리)
#     NIKON_OC_PIN_AUTH = 0x935a  # PIN 인증 (AP 모드에서만 사용)
#     NIKON_OC_UNKNOWN_944C = 0x944c  # 공식앱 Transaction ID: 1 (데이터 수신)
#     NIKON_OC_UNKNOWN_952A = 0x952a  # 공식앱 Transaction ID: 2 (데이터 전송)
#
#     # PTP 응답 코드 정의
#     PTP_RC_OK = 0x2001  # 성공
#     PTP_RC_GENERAL_ERROR = 0x2002  # 일반 오류
#     PTP_RC_SESSION_NOT_OPEN = 0x2003  # 세션이 열려있지 않음
#     PTP_RC_INVALID_TRANSACTION_ID = 0x2004  # 잘못된 트랜잭션 ID
#     PTP_RC_OPERATION_NOT_SUPPORTED = 0x2005  # 지원되지 않는 오퍼레이션
#     PTP_RC_PARAMETER_NOT_SUPPORTED = 0x2006  # 지원되지 않는 매개변수
#     PTP_RC_INCOMPLETE_TRANSFER = 0x2007  # 불완전한 전송
#     PTP_RC_INVALID_STORAGE_ID = 0x2008  # 잘못된 저장소 ID
#     PTP_RC_INVALID_OBJECT_HANDLE = 0x2009  # 잘못된 객체 핸들
#     PTP_RC_DEVICE_PROP_NOT_SUPPORTED = 0x200A  # 지원되지 않는 장치 속성
#     PTP_RC_INVALID_OBJECT_FORMAT_CODE = 0x200B  # 잘못된 객체 형식 코드
#     PTP_RC_STORAGE_FULL = 0x200C  # 저장소 가득 찬
#     PTP_RC_OBJECT_WRITE_PROTECTED = 0x200D  # 객체 쓰기 보호됨
#     PTP_RC_STORE_READ_ONLY = 0x200E  # 저장소 읽기 전용
#     PTP_RC_ACCESS_DENIED = 0x200F  # 접근 거부
#     PTP_RC_NO_THUMBNAIL_PRESENT = 0x2010  # 썸네일 없음
#     PTP_RC_SELF_TEST_FAILED = 0x2011  # 자가 진단 실패
#     PTP_RC_PARTIAL_DELETION = 0x2012  # 부분 삭제
#     PTP_RC_STORE_NOT_AVAILABLE = 0x2013  # 저장소 사용 불가
#     PTP_RC_SPECIFICATION_BY_FORMAT_UNSUPPORTED = 0x2014  # 형식 지정 지원 안함
#     PTP_RC_NO_VALID_OBJECT_INFO = 0x2015  # 유효한 객체 정보 없음
#     PTP_RC_INVALID_CODE_FORMAT = 0x2016  # 잘못된 코드 형식
#     PTP_RC_UNKNOWN_VENDOR_CODE = 0x2017  # 알 수 없는 벤더 코드
#     PTP_RC_CAPTURE_ALREADY_TERMINATED = 0x2018  # 캡처 이미 종료됨
#     PTP_RC_DEVICE_BUSY = 0x2019  # 장치 사용 중
#     PTP_RC_INVALID_PARENT_OBJECT = 0x201A  # 잘못된 부모 객체
#     PTP_RC_INVALID_DEVICE_PROP_FORMAT = 0x201B  # 잘못된 장치 속성 형식
#     PTP_RC_INVALID_DEVICE_PROP_VALUE = 0x201C  # 잘못된 장치 속성 값
#     PTP_RC_INVALID_PARAMETER = 0x201D  # 잘못된 매개변수
#     PTP_RC_SESSION_ALREADY_OPEN = 0x201E  # 세션 이미 열림
#     PTP_RC_TRANSACTION_CANCELLED = 0x201F  # 트랜잭션 취소됨
#     PTP_RC_SPECIFICATION_OF_DESTINATION_UNSUPPORTED = 0x2020  # 목적지 지정 지원 안함
#
#     # PTP 이벤트 코드 정의
#     PTP_EC_DeviceInfoChanged = 0x4008  # 장치 정보 변경 이벤트
#
#     # 실제 패킷 로그에서 관찰된 오퍼레이션 순서 (STA 모드)
#     # 1. GetDeviceInfo (0x1001) - Transaction ID: 0
#     # 2. OpenSession (0x1002) - Transaction ID: 0
#     # 3. Unknown_944C (0x944c) - Transaction ID: 1 (데이터 수신)
#     # 4. Unknown_952A (0x952a) - Transaction ID: 2 (PIN 관련 또는 다른 설정)
#     # 5. GetDeviceInfo (0x1001) - Transaction ID: 0 (재연결 시)
#     # 6. OpenSession (0x1002) - Transaction ID: 0 (재연결 시)
#     # 7. Unknown_944C (0x944c) - Transaction ID: 1 (재연결 후)
#     # 8. Unknown_952A (0x952a) - Transaction ID: 2 (재연결 후)
#
#     def __init__(self, camera_ip: str, camera_port: int = 15740):
#         """
#         PTP/IP 클라이언트 초기화
#
#         Args:
#             camera_ip: 카메라 IP 주소
#             camera_port: 카메라 포트 번호 (기본값: 15740)
#         """
#         logger.info(f"PTP/IP 클라이언트 초기화 시작 - IP: {camera_ip}, 포트: {camera_port}")
#
#         # 연결 설정
#         self.camera_ip = camera_ip
#         self.camera_port = camera_port
#
#         self.command_socket: Optional[socket.socket] = None  # 명령 채널 소켓
#         self.event_socket: Optional[socket.socket] = None  # 이벤트 채널 소켓
#
#         # 세션 및 트랜잭션 관리
#         self.session_id = 1  # 세션 ID
#         self.transaction_id = 0  # 트랜잭션 ID (패킷 로그에서 0부터 시작)
#         self.connection_number = 1  # 연결 번호
#
#         # 클라이언트 식별 정보
#         # 패킷 로그에서 관찰된 실제 GUID와 이름 사용 (안드로이드 앱)
#         self.client_guid = bytes.fromhex('e9dca7d89c7b440dba010f9e04c0ec23')  # 안드로이드 앱 GUID
#         self.client_name = "Android Device"  # 안드로이드 디바이스 이름
#
#         # 이벤트 처리 관련
#         self.event_thread: Optional[threading.Thread] = None  # 이벤트 모니터링 스레드
#         self.event_received = threading.Event()  # 이벤트 수신 신호
#         self.device_info_changed = False  # 장치 정보 변경 플래그
#
#         logger.info(f"클라이언트 GUID 설정: {self.client_guid.hex()}")
#         logger.info(f"클라이언트 이름 설정: {self.client_name}")
#         logger.info("PTP/IP 클라이언트 초기화 완료")
#
#     def connect(self) -> bool:
#         """카메라에 연결하고 명령 및 이벤트 채널을 설정"""
#         logger.info("카메라 연결 시도 중...")
#
#         try:
#             # 명령 채널 생성
#             logger.info("명령 채널 소켓 생성 중...")
#             self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             self.command_socket.settimeout(10)  # 10초 타임아웃 설정
#             logger.debug(f"명령 채널 소켓 생성 완료 - 타임아웃: 10초")
#
#             # 소켓 옵션 설정 (공식앱과 동일한 설정 시도)
#             self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#             self.command_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
#             logger.debug("소켓 옵션 설정 완료 (SO_REUSEADDR, TCP_NODELAY)")
#
#             logger.info(f"명령 채널 연결 시도: {self.camera_ip}:{self.camera_port}")
#             logger.debug("TCP 연결 시작...")
#             self.command_socket.connect((self.camera_ip, self.camera_port))
#             logger.info("✅ 명령 채널 TCP 연결 성공!")
#
#             # 명령 채널 초기화 요청 전송
#             logger.info("명령 채널 PTP/IP 초기화 시작...")
#             if not self._send_init_command_request():
#                 logger.error("명령 채널 초기화 실패")
#                 return False
#
#             # 이벤트 채널 생성
#             logger.info("이벤트 채널 소켓 생성 중...")
#             self.event_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             self.event_socket.settimeout(10)  # 10초 타임아웃 설정
#             logger.debug(f"이벤트 채널 소켓 생성 완료 - 타임아웃: 10초")
#
#             logger.info(f"이벤트 채널 연결 시도: {self.camera_ip}:{self.camera_port}")
#             logger.debug("TCP 연결 시작...")
#             self.event_socket.connect((self.camera_ip, self.camera_port))
#             logger.info("✅ 이벤트 채널 TCP 연결 성공!")
#
#             # 이벤트 채널 초기화 요청 전송
#             logger.info("이벤트 채널 PTP/IP 초기화 시작...")
#             if not self._send_init_event_request():
#                 logger.error("이벤트 채널 초기화 실패")
#                 return False
#
#             # 이벤트 모니터링 스레드 시작
#             logger.info("이벤트 모니터링 스레드 시작 중...")
#             self.event_thread = threading.Thread(target=self._monitor_events, daemon=True)
#             self.event_thread.start()
#             logger.info("이벤트 모니터링 스레드 시작 완료")
#
#             logger.info("🎉 카메라 연결 완료!")
#             return True
#
#         except socket.timeout:
#             logger.error("❌ 연결 타임아웃 발생 (10초)")
#             logger.error("   → 카메라가 응답하지 않습니다")
#             return False
#         except ConnectionRefusedError:
#             logger.error("❌ 연결 거부됨")
#             logger.error("   → 카메라 IP 주소나 포트를 확인하세요")
#             logger.error("   → 카메라의 Wi-Fi 설정을 확인하세요")
#             return False
#         except OSError as e:
#             if "No route to host" in str(e):
#                 logger.error("❌ 호스트에 도달할 수 없음")
#                 logger.error("   → 네트워크 연결을 확인하세요")
#                 logger.error("   → 카메라가 같은 네트워크에 있는지 확인하세요")
#             else:
#                 logger.error(f"❌ 네트워크 오류: {e}")
#             return False
#         except Exception as e:
#             logger.error(f"❌ 예상치 못한 연결 실패: {e}")
#             logger.debug("연결 실패 상세 정보:", exc_info=True)
#             return False
#
#     def _send_init_command_request(self) -> bool:
#         """명령 채널 초기화 요청을 전송하고 응답을 대기"""
#         logger.info("📤 명령 채널 초기화 요청 전송 중...")
#
#         # 클라이언트 GUID와 이름 준비
#         name_utf16 = (self.client_name + '\0').encode('utf-16le')
#         logger.debug(f"클라이언트 이름 UTF-16LE 인코딩: {name_utf16.hex()}")
#
#         # 명령 채널 초기화 요청 패킷 생성
#         packet_length = 8 + 16 + len(name_utf16)
#         packet = struct.pack('<II',
#                              packet_length,  # 패킷 길이
#                              self.PTPIP_INIT_COMMAND_REQUEST)  # 패킷 타입
#         packet += self.client_guid  # 클라이언트 GUID (16바이트)
#         packet += name_utf16  # 클라이언트 이름 (UTF-16LE)
#
#         logger.info(f"📤 전송할 패킷 정보:")
#         logger.info(f"   길이: {packet_length} 바이트")
#         logger.info(f"   타입: PTPIP_INIT_COMMAND_REQUEST ({self.PTPIP_INIT_COMMAND_REQUEST})")
#         logger.info(f"   GUID: {self.client_guid.hex()}")
#         logger.info(f"   이름: {self.client_name}")
#         logger.debug(f"📤 전체 패킷 데이터: {packet.hex()}")
#
#         # 패킷 전송
#         try:
#             logger.debug("📤 패킷 전송 시작...")
#             bytes_sent = self.command_socket.send(packet)
#             logger.info(f"📤 패킷 전송 완료: {bytes_sent}/{len(packet)} 바이트")
#         except Exception as e:
#             logger.error(f"❌ 패킷 전송 실패: {e}")
#             return False
#
#         # 명령 채널 초기화 응답 수신
#         try:
#             logger.info("📥 명령 채널 초기화 응답 대기 중...")
#             logger.debug("📥 recv() 호출...")
#             response = self.command_socket.recv(1024)
#             logger.info(f"📥 응답 데이터 수신: {len(response)} 바이트")
#             logger.debug(f"📥 응답 원본 데이터: {response.hex()}")
#
#             if len(response) < 8:
#                 logger.error("❌ 응답 데이터가 너무 짧음 (최소 8바이트 필요)")
#                 logger.error(f"   실제 수신: {len(response)} 바이트")
#                 return False
#
#             # 응답 헤더 파싱
#             length, packet_type = struct.unpack('<II', response[:8])
#             logger.info(f"📥 응답 패킷 정보:")
#             logger.info(f"   길이: {length} 바이트")
#             logger.info(f"   타입: {packet_type}")
#
#             if packet_type == self.PTPIP_INIT_COMMAND_ACK:
#                 logger.info("✅ 명령 채널 초기화 응답 수신 성공 (PTPIP_INIT_COMMAND_ACK)")
#
#                 # 연결 번호 및 카메라 정보 추출
#                 if len(response) >= 12:
#                     self.connection_number = struct.unpack('<I', response[8:12])[0]
#                     logger.info(f"📥 연결 번호 수신: {self.connection_number}")
#
#                     # 카메라 이름 추출 (있는 경우)
#                     if len(response) > 12:
#                         try:
#                             camera_name_data = response[12:]
#                             logger.debug(f"카메라 이름 원본 데이터: {camera_name_data.hex()}")
#                             # UTF-16LE로 디코딩 시도
#                             camera_name = camera_name_data.decode('utf-16le', errors='ignore').rstrip('\x00')
#                             if camera_name:
#                                 logger.info(f"📥 카메라 이름: {camera_name}")
#                         except Exception as e:
#                             logger.debug(f"카메라 이름 추출 실패: {e}")
#                 else:
#                     logger.warning("연결 번호 데이터 부족")
#
#                 return True
#
#             elif packet_type == self.PTPIP_INIT_FAIL:
#                 logger.error("❌ 명령 채널 초기화 실패 응답 수신 (PTPIP_INIT_FAIL)")
#                 # 실패 사유 코드 추출 (있는 경우)
#                 if len(response) >= 12:
#                     fail_reason = struct.unpack('<I', response[8:12])[0]
#                     logger.error(f"   실패 사유 코드: {fail_reason}")
#                 return False
#
#             else:
#                 logger.error(f"❌ 예상치 못한 응답 타입: {packet_type}")
#                 logger.error("   예상: PTPIP_INIT_COMMAND_ACK (2) 또는 PTPIP_INIT_FAIL (5)")
#                 return False
#
#         except socket.timeout:
#             logger.error("❌ 명령 채널 초기화 응답 수신 타임아웃")
#             logger.error("   → 카메라가 응답하지 않습니다")
#             return False
#         except Exception as e:
#             logger.error(f"❌ 명령 채널 초기화 응답 수신 중 오류: {e}")
#             logger.debug("응답 수신 오류 상세:", exc_info=True)
#             return False
#
#     def _send_init_event_request(self) -> bool:
#         """이벤트 채널 초기화 요청을 전송하고 응답을 대기"""
#         logger.info("이벤트 채널 초기화 요청 전송 중...")
#
#         # 이벤트 채널 초기화 요청 패킷 생성
#         packet = struct.pack('<III',
#                              12,  # 패킷 길이
#                              self.PTPIP_INIT_EVENT_REQUEST,  # 패킷 타입
#                              self.connection_number)  # 연결 번호
#
#         logger.debug(f"연결 번호: {self.connection_number}")
#         logger.debug(f"패킷 데이터: {packet.hex()}")
#
#         # 패킷 전송
#         try:
#             self.event_socket.send(packet)
#             logger.info("이벤트 채널 초기화 요청 전송 완료")
#         except Exception as e:
#             logger.error(f"이벤트 채널 초기화 요청 전송 실패: {e}")
#             return False
#
#         # 이벤트 채널 초기화 응답 수신
#         try:
#             logger.info("이벤트 채널 초기화 응답 대기 중...")
#             response = self.event_socket.recv(1024)
#             logger.debug(f"응답 데이터 수신: {len(response)} 바이트")
#             logger.debug(f"응답 데이터: {response.hex()}")
#
#             if len(response) < 8:
#                 logger.error("응답 데이터가 너무 짧음")
#                 return False
#
#             # 응답 헤더 파싱
#             length, packet_type = struct.unpack('<II', response[:8])
#             logger.debug(f"응답 패킷 길이: {length}, 타입: {packet_type}")
#
#             if packet_type == self.PTPIP_INIT_EVENT_ACK:
#                 logger.info("이벤트 채널 초기화 응답 수신 성공")
#                 return True
#             else:
#                 logger.error(f"예상치 못한 이벤트 응답 타입: {packet_type}")
#                 return False
#
#         except socket.timeout:
#             logger.error("이벤트 채널 초기화 응답 수신 타임아웃")
#             return False
#         except Exception as e:
#             logger.error(f"이벤트 채널 초기화 응답 수신 중 오류: {e}")
#             return False
#
#     def _monitor_events(self):
#         """카메라로부터 이벤트를 모니터링하는 메서드"""
#         logger.info("이벤트 모니터링 시작...")
#
#         while True:
#             try:
#                 # 이벤트 데이터 수신
#                 data = self.event_socket.recv(1024)
#                 if not data:
#                     logger.warning("이벤트 소켓에서 데이터 수신 중단")
#                     break
#
#                 logger.debug(f"이벤트 데이터 수신: {len(data)} 바이트")
#                 logger.debug(f"이벤트 데이터: {data.hex()}")
#
#                 # 최소 헤더 크기 확인
#                 if len(data) >= 8:
#                     length, packet_type = struct.unpack('<II', data[:8])
#                     logger.debug(f"이벤트 패킷 길이: {length}, 타입: {packet_type}")
#
#                     # 이벤트 패킷 처리
#                     if packet_type == self.PTPIP_EVENT and len(data) >= 18:
#                         # 이벤트 정보 파싱
#                         event_code = struct.unpack('<H', data[12:14])[0]
#                         transaction_id = struct.unpack('<I', data[14:18])[0]
#                         logger.info(f"이벤트 수신: 코드=0x{event_code:04x}, 트랜잭션ID={transaction_id}")
#
#                         # 특정 이벤트 처리
#                         if event_code == self.PTP_EC_DeviceInfoChanged:
#                             logger.info("장치 정보 변경 이벤트 수신 - 모든 기능 사용 가능!")
#                             self.device_info_changed = True
#                             self.event_received.set()
#                         else:
#                             logger.info(f"알 수 없는 이벤트 코드: 0x{event_code:04x}")
#
#                         # 이벤트에 추가 데이터가 있는 경우 처리
#                         if len(data) > 18:
#                             additional_data = data[18:]
#                             logger.debug(f"이벤트 추가 데이터: {additional_data.hex()}")
#
#                     else:
#                         logger.debug(f"알 수 없는 패킷 타입: {packet_type}")
#
#                 else:
#                     logger.warning("수신된 이벤트 데이터가 너무 짧음")
#
#             except socket.timeout:
#                 logger.debug("이벤트 모니터링 타임아웃 (정상)")
#                 continue
#             except Exception as e:
#                 logger.error(f"이벤트 모니터링 중 오류 발생: {e}")
#                 break
#
#         logger.info("이벤트 모니터링 종료")
#
#     def _get_operation_name(self, op_code: int) -> str:
#         """오퍼레이션 코드의 이름을 반환하는 메서드"""
#         op_names = {
#             # 표준 PTP 오퍼레이션 코드
#             0x1001: "GetDeviceInfo",
#             0x1002: "OpenSession",
#             0x1003: "CloseSession",
#             0x1004: "GetStorageIDs",
#             0x1005: "GetStorageInfo",
#             0x1006: "GetNumObjects",
#             0x1007: "GetObjectHandles",
#             0x1008: "GetObjectInfo",
#             0x1009: "GetObject",
#             0x100A: "GetThumb",
#             0x100B: "DeleteObject",
#             0x100C: "SendObjectInfo",
#             0x100D: "SendObject",
#             0x100E: "InitiateCapture",
#             0x100F: "FormatStore",
#             0x1010: "ResetDevice",
#             0x1011: "SelfTest",
#             0x1012: "SetObjectProtection",
#             0x1013: "PowerDown",
#             0x1014: "GetDevicePropDesc",
#             0x1015: "GetDevicePropValue",
#             0x1016: "SetDevicePropValue",
#             0x1017: "ResetDevicePropValue",
#             0x1018: "TerminateOpenCapture",
#             0x1019: "MoveObject",
#             0x101A: "CopyObject",
#             0x101B: "GetPartialObject",
#             0x101C: "InitiateOpenCapture",
#
#             # 니콘 전용 오퍼레이션 코드
#             0x935a: "PIN_AUTH (Nikon)",
#             0x944c: "Unknown_944C (Nikon)",
#             0x952a: "Unknown_952A (Nikon)"
#         }
#         return op_names.get(op_code, f"Unknown(0x{op_code:04x})")
#
#     def _parse_multiple_ptpip_packets(self, data: bytes) -> Tuple[bytes, int, bytes]:
#         """
#         하나의 TCP 패킷에 포함된 여러 PTP/IP 패킷을 파싱
#         Returns: (data_payload, response_code, remaining_data)
#         """
#         offset = 0
#         data_payload = b''
#         response_code = 0
#
#         logger.debug(f"🔍 다중 PTP/IP 패킷 파싱 시작: {len(data)} 바이트")
#         logger.debug(f"🔍 원본 데이터: {data.hex()}")
#
#         while offset < len(data):
#             if offset + 8 > len(data):
#                 break
#
#             # PTP/IP 헤더 파싱
#             length, packet_type = struct.unpack('<II', data[offset:offset + 8])
#             logger.debug(f"🔍 오프셋 {offset}: 길이={length}, 타입={packet_type}")
#
#             if offset + length > len(data):
#                 logger.warning(f"⚠️ 패킷 길이 초과: 필요={length}, 남은={len(data) - offset}")
#                 break
#
#             packet_data = data[offset:offset + length]
#
#             if packet_type == self.PTPIP_START_DATA_PACKET:
#                 logger.debug("📥 Start Data Packet 발견")
#                 if length >= 20:
#                     expected_size = struct.unpack('<Q', packet_data[12:20])[0]
#                     logger.debug(f"📥 예상 데이터 크기: {expected_size} 바이트")
#                     # Start Data Packet에는 보통 헤더만 있고 실제 데이터는 End Data에 있음
#                     if length > 20:
#                         start_payload = packet_data[20:]
#                         if start_payload:  # 실제 데이터가 있는 경우만 추가
#                             data_payload += start_payload
#                             logger.debug(f"📥 Start Data에서 {len(start_payload)} 바이트 추출")
#
#             elif packet_type == self.PTPIP_END_DATA_PACKET:
#                 logger.debug("📥 End Data Packet 발견")
#                 # End Data Packet 구조: [길이(4)] [타입(4)] [트랜잭션ID(4)] [실제데이터...]
#                 # 헤더는 12바이트가 아니라 20바이트 (길이+타입+트랜잭션ID+데이터 크기)
#                 header_size = 12  # PTP/IP End Data Packet 헤더는 12바이트
#                 if length > header_size:
#                     end_payload = packet_data[header_size:]
#                     data_payload += end_payload
#                     logger.debug(f"📥 End Data에서 {len(end_payload)} 바이트 추출")
#                     logger.debug(f"📥 End Data 헤더 크기: {header_size} 바이트")
#                     logger.debug(f"📥 End Data 전체 길이: {length} 바이트")
#                 elif length == header_size:
#                     logger.debug("📥 End Data는 헤더만 있음 (데이터는 Start Data에서 추출됨)")
#
#             elif packet_type == self.PTPIP_CMD_RESPONSE:
#                 logger.debug("📥 Command Response 발견")
#                 if length >= 14:
#                     response_code = struct.unpack('<H', packet_data[8:10])[0]
#                     transaction_id = struct.unpack('<I', packet_data[10:14])[0]
#                     logger.info(f"📥 CMD_RESPONSE: 코드=0x{response_code:04x}, 트랜잭션={transaction_id}")
#
#             offset += length
#
#         logger.debug(f"🔍 파싱 완료: 데이터={len(data_payload)}바이트, 응답=0x{response_code:04x}")
#         logger.debug(f"🔍 추출된 데이터: {data_payload[:50].hex()}...")
#         return data_payload, response_code, data[offset:] if offset < len(data) else b''
#
#     def _send_ptp_command_with_data(self, op_code: int, parameters: List[int] = None, data_to_send: bytes = b'') -> Tuple[int, bytes]:
#         """데이터와 함께 PTP 명령을 전송하고 응답 코드와 데이터를 반환"""
#         if parameters is None:
#             parameters = []
#
#         logger.info(f"데이터와 함께 PTP 명령 전송: {self._get_operation_name(op_code)} (0x{op_code:04x}) (트랜잭션ID: {self.transaction_id})")
#         logger.debug(f"명령 매개변수: {parameters}")
#         logger.debug(f"전송할 데이터 크기: {len(data_to_send)} 바이트")
#
#         # 1단계: 명령 요청 패킷 전송 (패킷 분석에서 30바이트)
#         packet_length = 30  # 성공한 앱에서 관찰된 길이
#         packet = struct.pack('<II',
#                              packet_length,  # 패킷 길이
#                              self.PTPIP_CMD_REQUEST)  # 패킷 타입
#         packet += struct.pack('<IHI', 2, op_code, self.transaction_id)  # data_phase=2 (송신)
#
#         # 매개변수 추가 (12바이트를 채우기 위해)
#         for i, param in enumerate(parameters):
#             packet += struct.pack('<I', param)
#
#         # 나머지 공간을 0으로 채움
#         while len(packet) < packet_length:
#             packet += b'\x00'
#
#         logger.debug(f"명령 패킷 데이터: {packet.hex()}")
#
#         try:
#             bytes_sent = self.command_socket.send(packet)
#             logger.info(f"📤 명령 패킷 전송 완료: {bytes_sent}/{len(packet)} 바이트")
#         except Exception as e:
#             logger.error(f"명령 패킷 전송 실패: {e}")
#             self.transaction_id += 1
#             return 0, b''
#
#         # 2단계: Start Data Packet 전송
#         start_data_length = 20
#         start_packet = struct.pack('<III', start_data_length, self.PTPIP_START_DATA_PACKET, self.transaction_id)
#         start_packet += struct.pack('<Q', len(data_to_send))  # 전송할 데이터 크기
#
#         try:
#             bytes_sent = self.command_socket.send(start_packet)
#             logger.info(f"📤 Start Data 패킷 전송 완료: {bytes_sent}/{len(start_packet)} 바이트")
#         except Exception as e:
#             logger.error(f"Start Data 패킷 전송 실패: {e}")
#             self.transaction_id += 1
#             return 0, b''
#
#         # 3단계: End Data Packet 전송 (실제 데이터 포함)
#         end_data_length = 12 + len(data_to_send)
#         end_packet = struct.pack('<III', end_data_length, self.PTPIP_END_DATA_PACKET, self.transaction_id)
#         end_packet += data_to_send
#
#         try:
#             bytes_sent = self.command_socket.send(end_packet)
#             logger.info(f"📤 End Data 패킷 전송 완료: {bytes_sent}/{len(end_packet)} 바이트")
#         except Exception as e:
#             logger.error(f"End Data 패킷 전송 실패: {e}")
#             self.transaction_id += 1
#             return 0, b''
#
#         # 4단계: 응답 수신 - 0x944c는 특별 처리
#         response_code = 0
#         response_data = b''
#
#         if op_code == self.NIKON_OC_UNKNOWN_944C:
#             try:
#                 logger.info("📥 0x944c 특별 처리: 카메라에서 데이터 전송 대기 중...")
#
#                 # 모든 응답 패킷을 한 번에 수신할 수 있음
#                 logger.info("📥 응답 패킷들 수신 중...")
#                 self.command_socket.settimeout(10)
#                 all_data = self.command_socket.recv(4096)
#                 logger.info(f"📥 전체 응답 수신: {len(all_data)} 바이트")
#                 logger.debug(f"📥 전체 데이터: {all_data.hex()}")
#
#                 # 다중 패킷 파싱 사용
#                 response_data, response_code, remaining = self._parse_multiple_ptpip_packets(all_data)
#
#                 # 응답 코드가 0이면 추가 데이터 수신 시도
#                 if response_code == 0 and remaining:
#                     logger.info("📥 추가 응답 데이터 처리 중...")
#                     additional_data, additional_code, _ = self._parse_multiple_ptpip_packets(remaining)
#                     if additional_code != 0:
#                         response_code = additional_code
#
#                 # 여전히 응답 코드가 0이면 별도로 Operation Response 수신
#                 if response_code == 0:
#                     try:
#                         logger.info("📥 Operation Response 별도 수신 중...")
#                         cmd_response = self.command_socket.recv(1024)
#                         logger.info(f"📥 Operation Response 수신: {len(cmd_response)} 바이트")
#                         logger.debug(f"📥 Operation Response: {cmd_response.hex()}")
#
#                         if len(cmd_response) >= 14:
#                             length, packet_type = struct.unpack('<II', cmd_response[:8])
#                             if packet_type == self.PTPIP_CMD_RESPONSE:
#                                 response_code = struct.unpack('<H', cmd_response[8:10])[0]
#                                 transaction_id = struct.unpack('<I', cmd_response[10:14])[0]
#                                 logger.info(f"📥 별도 응답: 코드=0x{response_code:04x}, 트랜잭션={transaction_id}")
#                     except socket.timeout:
#                         logger.warning("⚠️ Operation Response 별도 수신 타임아웃")
#
#                 logger.info(f"📥 0x944c 최종 결과: 응답=0x{response_code:04x}, 데이터={len(response_data)}바이트")
#
#             except socket.timeout:
#                 logger.error("❌ 0x944c 응답 수신 타임아웃")
#             except Exception as e:
#                 logger.error(f"❌ 0x944c 처리 중 오류: {e}")
#                 logger.debug("0x944c 오류 상세:", exc_info=True)
#         else:
#             # 기존 로직: 일반적인 PTP 명령 처리
#             try:
#                 logger.info("📥 응답 수신 대기 중...")
#
#                 data_phase = 1 if op_code in [
#                     self.PTP_OC_GetDeviceInfo,
#                     self.PTP_OC_GetStorageIDs,
#                     self.PTP_OC_GetStorageInfo,
#                     self.PTP_OC_GetObjectHandles,
#                     self.PTP_OC_GetObjectInfo,
#                     self.PTP_OC_GetObject,
#                     self.PTP_OC_GetThumb,
#                     self.PTP_OC_GetDevicePropDesc,
#                     self.PTP_OC_GetDevicePropValue,
#                     self.PTP_OC_GetPartialObject,
#                     self.NIKON_OC_UNKNOWN_944C  # 니콘 전용 - 데이터 수신
#                 ] else 0
#                 logger.debug(f"데이터 수신 예상: {'예' if data_phase else '아니오'}")
#
#                 if data_phase == 1:
#                     # 데이터가 있는 명령: 여러 패킷이 함께 올 수 있음
#                     logger.info("📥 데이터 응답 수신 중...")
#                     self.command_socket.settimeout(10)
#                     raw_response = self.command_socket.recv(4096)
#                     logger.info(f"📥 원본 응답 수신: {len(raw_response)} 바이트")
#                     logger.debug(f"📥 원본 데이터: {raw_response.hex()}")
#
#                     # 다중 패킷 파싱 사용
#                     response_data, response_code, remaining = self._parse_multiple_ptpip_packets(raw_response)
#
#                     if response_code == 0:
#                         # 응답이 없으면 별도로 수신
#                         logger.info("📥 명령 응답 별도 수신 중...")
#                         try:
#                             cmd_response = self.command_socket.recv(1024)
#                             logger.info(f"📥 명령 응답 수신: {len(cmd_response)} 바이트")
#                             logger.debug(f"📥 명령 응답 데이터: {cmd_response.hex()}")
#
#                             if len(cmd_response) >= 14:
#                                 length, packet_type = struct.unpack('<II', cmd_response[:8])
#                                 if packet_type == self.PTPIP_CMD_RESPONSE:
#                                     response_code = struct.unpack('<H', cmd_response[8:10])[0]
#                                     transaction_id = struct.unpack('<I', cmd_response[10:14])[0]
#                                     logger.info(f"📥 별도 응답: 코드=0x{response_code:04x}, 트랜잭션={transaction_id}")
#                         except socket.timeout:
#                             logger.warning("⚠️ 명령 응답 타임아웃")
#
#                 else:
#                     # 데이터가 없는 명령: 명령 응답만
#                     logger.info("📥 명령 응답만 수신 중...")
#                     self.command_socket.settimeout(10)
#                     cmd_response = self.command_socket.recv(1024)
#                     logger.info(f"📥 명령 응답 수신: {len(cmd_response)} 바이트")
#                     logger.debug(f"📥 명령 응답 데이터: {cmd_response.hex()}")
#
#                     if len(cmd_response) >= 14:
#                         length, packet_type = struct.unpack('<II', cmd_response[:8])
#                         if packet_type == self.PTPIP_CMD_RESPONSE:
#                             response_code = struct.unpack('<H', cmd_response[8:10])[0]
#                             transaction_id = struct.unpack('<I', cmd_response[10:14])[0]
#                             logger.info(f"📥 응답: 코드=0x{response_code:04x}, 트랜잭션={transaction_id}")
#
#             except socket.timeout:
#                 logger.error("❌ 응답 수신 타임아웃")
#             except Exception as e:
#                 logger.error(f"❌ 응답 수신 중 오류: {e}")
#                 logger.debug("응답 수신 오류 상세:", exc_info=True)
#
#         self.transaction_id += 1
#         return response_code, response_data
#
#     def _send_ptp_command(self, op_code: int, parameters: List[int] = None) -> Tuple[int, bytes]:
#         """PTP 명령을 전송하고 응답 코드와 데이터를 반환"""
#         if parameters is None:
#             parameters = []
#
#         logger.info(f"PTP 명령 전송 중: {self._get_operation_name(op_code)} (0x{op_code:04x}) (트랜잭션ID: {self.transaction_id})")
#         logger.debug(f"명령 매개변수: {parameters}")
#
#         # Frame 93 성공 패킷 구조를 정확히 복사 (30 bytes)
#         if op_code == self.NIKON_OC_UNKNOWN_944C:
#             logger.info(f"📤 Frame 93 성공 패킷 구조 사용 (트랜잭션ID: 1로 고정)")
#
#             # 0x944c는 항상 트랜잭션 ID 1을 사용해야 함 (성공 패킷 분석 결과)
#             transaction_id_to_use = 1
#
#             # Frame 93에서 관찰된 정확한 30바이트 구조
#             packet_length = 30  # Frame 93 Length 필드와 동일
#             packet = struct.pack('<II', packet_length, self.PTPIP_CMD_REQUEST)
#             packet += struct.pack('<IHI', 1, op_code, transaction_id_to_use)  # 트랜잭션 ID 1 고정
#
#             # Frame 93 실제 hex dump에서 발견된 정확한 12바이트 패딩
#             # 실제: 00 00 30 95 00 00 00 00 00 00 00 00
#             packet += struct.pack('<HHHHHH', 0x0000, 0x9530, 0x0000, 0x0000, 0x0000, 0x0000)
#
#             logger.debug(f"명령 패킷 길이: {len(packet)} 바이트")
#             logger.debug(f"명령 패킷 데이터: {packet.hex()}")
#
#             # Frame 93과 정확히 동일한 패킷인지 확인
#             expected_packet = "1e00000006000000010000004c94010000003095000000000000000000000000"
#             actual_hex = packet.hex()
#             logger.debug(f"예상 패킷: {expected_packet}")
#             logger.debug(f"실제 패킷: {actual_hex}")
#
#             if actual_hex == expected_packet:
#                 logger.info("✅ Frame 93과 완전히 동일한 패킷 생성!")
#             else:
#                 logger.warning("⚠️ Frame 93과 불일치")
#
#         # Frame 40 구조로 0x952b 패킷 생성 (데이터 수신)
#         elif op_code == 0x952b:
#             logger.info(f"📤 Frame 40 구조로 0x952b 패킷 생성 (트랜잭션ID: 1로 고정)")
#
#             # Frame 40은 Transaction ID 1, 18바이트 패킷, 데이터 수신
#             transaction_id_to_use = 1
#             packet_length = 18
#             packet = struct.pack('<II', packet_length, self.PTPIP_CMD_REQUEST)
#             packet += struct.pack('<IHI', 1, op_code, transaction_id_to_use)  # data_phase=1 (수신)
#
#             logger.debug(f"0x952b 명령 패킷: {packet.hex()}")
#             logger.info("✅ Frame 40과 동일한 0x952b 패킷 구성!")
#
#         else:
#             # 기존 로직: 일반적인 PTP 명령
#             data_phase = 1 if op_code in [
#                 self.PTP_OC_GetDeviceInfo,
#                 self.PTP_OC_GetStorageIDs,
#                 self.PTP_OC_GetStorageInfo,
#                 self.PTP_OC_GetObjectHandles,
#                 self.PTP_OC_GetObjectInfo,
#                 self.PTP_OC_GetObject,
#                 self.PTP_OC_GetThumb,
#                 self.PTP_OC_GetDevicePropDesc,
#                 self.PTP_OC_GetDevicePropValue,
#                 self.PTP_OC_GetPartialObject,
#                 self.NIKON_OC_UNKNOWN_944C,
#                 0x952b  # 0x952b도 데이터 수신 오퍼레이션
#             ] else 0
#
#             packet_length = 18 + len(parameters) * 4
#             packet = struct.pack('<II', packet_length, self.PTPIP_CMD_REQUEST)
#             packet += struct.pack('<IHI', data_phase, op_code, self.transaction_id)
#
#             # 매개변수 추가
#             for param in parameters:
#                 packet += struct.pack('<I', param)
#
#             logger.debug(f"명령 패킷 길이: {len(packet)} 바이트")
#             logger.debug(f"명령 패킷 데이터: {packet.hex()}")
#
#         # 패킷 전송
#         try:
#             bytes_sent = self.command_socket.send(packet)
#             logger.info(f"📤 패킷 전송 완료: {bytes_sent}/{len(packet)} 바이트")
#         except Exception as e:
#             logger.error(f"PTP 명령 전송 실패: {e}")
#             self.transaction_id += 1
#             return 0, b''
#
#         # 응답 수신 - PTP/IP 사양에 따른 올바른 처리
#         response_data = b''
#         response_code = 0
#
#         try:
#             logger.info("📥 응답 수신 대기 중...")
#             self.command_socket.settimeout(10)
#
#             # 첫 번째 응답 수신
#             raw_response = self.command_socket.recv(4096)
#             logger.info(f"📥 응답 수신: {len(raw_response)} 바이트")
#             logger.debug(f"📥 응답 데이터: {raw_response.hex()}")
#
#             if len(raw_response) < 8:
#                 logger.error("응답 데이터가 너무 짧음")
#                 self.transaction_id += 1
#                 return 0, b''
#
#             # PTP/IP 헤더 파싱
#             length, packet_type = struct.unpack('<II', raw_response[:8])
#             logger.debug(f"📥 패킷 길이: {length}, 타입: {packet_type}")
#
#             if packet_type == self.PTPIP_CMD_RESPONSE:
#                 # Type 7: CMD_RESPONSE - [길이:4] [타입:4] [응답코드:2] [트랜잭션ID:4] [매개변수들...]
#                 if length >= 14:
#                     response_code = struct.unpack('<H', raw_response[8:10])[0]
#                     transaction_id = struct.unpack('<I', raw_response[10:14])[0]
#                     logger.info(f"📥 CMD_RESPONSE: 코드=0x{response_code:04x}, 트랜잭션={transaction_id}")
#
#                     # 추가 매개변수가 있는 경우 파싱
#                     if length > 14:
#                         params_data = raw_response[14:length]
#                         logger.debug(f"📥 응답 매개변수: {params_data.hex()}")
#
#             elif packet_type == self.PTPIP_START_DATA_PACKET:
#                 # Type 9: START_DATA_PACKET이 먼저 온 경우
#                 logger.debug("📥 Start Data Packet 수신")
#                 response_data, response_code, _ = self._parse_multiple_ptpip_packets(raw_response)
#
#                 # CMD_RESPONSE가 별도로 올 수 있음
#                 if response_code == 0:
#                     try:
#                         cmd_response = self.command_socket.recv(1024)
#                         logger.info(f"📥 추가 CMD_RESPONSE 수신: {len(cmd_response)} 바이트")
#                         logger.debug(f"📥 CMD_RESPONSE 데이터: {cmd_response.hex()}")
#
#                         if len(cmd_response) >= 14:
#                             cmd_length, cmd_type = struct.unpack('<II', cmd_response[:8])
#                             if cmd_type == self.PTPIP_CMD_RESPONSE:
#                                 response_code = struct.unpack('<H', cmd_response[8:10])[0]
#                                 transaction_id = struct.unpack('<I', cmd_response[10:14])[0]
#                                 logger.info(f"📥 추가 응답: 코드=0x{response_code:04x}, 트랜잭션={transaction_id}")
#                     except socket.timeout:
#                         logger.debug("추가 응답 타임아웃 (정상)")
#
#             else:
#                 logger.warning(f"예상치 못한 패킷 타입: {packet_type}")
#
#         except socket.timeout:
#             logger.error("❌ 응답 수신 타임아웃")
#         except Exception as e:
#             logger.error(f"❌ 응답 수신 중 오류: {e}")
#             logger.debug("응답 수신 오류 상세:", exc_info=True)
#
#         # 결과 로깅
#         logger.info(f"📥 명령 응답: {self._get_operation_name(op_code)} 완료")
#         logger.info(f"   응답 코드: 0x{response_code:04x}")
#         logger.info(f"   트랜잭션ID: {self.transaction_id}")
#
#         if response_code == self.PTP_RC_OK:
#             logger.info("✅ 명령 실행 성공")
#             if response_data:
#                 logger.info(f"✅ 데이터 수신 완료: {len(response_data)} 바이트")
#         else:
#             logger.warning(f"❌ 명령 실행 실패: 응답 코드 0x{response_code:04x}")
#
#         self.transaction_id += 1
#         return response_code, response_data
#
#     def get_device_info(self) -> Optional[dict]:
#         """장치 정보를 가져오는 메서드"""
#         logger.info("장치 정보 요청 시작")
#         logger.info("=" * 50)
#
#         response_code, data = self._send_ptp_command(self.PTP_OC_GetDeviceInfo)
#
#         if response_code == self.PTP_RC_OK and data:
#             logger.info("장치 정보 수신 성공")
#             return self._parse_device_info(data)
#         else:
#             logger.error(f"장치 정보 가져오기 실패: 응답 코드 0x{response_code:04x}")
#             return None
#
#     def _parse_device_info(self, data: bytes) -> dict:
#         """장치 정보 데이터를 파싱하는 메서드"""
#         logger.info("장치 정보 파싱 시작")
#         logger.debug(f"파싱할 데이터 크기: {len(data)} 바이트")
#         logger.debug(f"전체 데이터 hex: {data.hex()}")
#
#         if len(data) < 8:
#             logger.error("장치 정보 데이터가 너무 짧음")
#             return {}
#
#         try:
#             # PTP DeviceInfo 구조 파싱
#             offset = 0
#
#             # Standard Version (2바이트)
#             standard_version = struct.unpack('<H', data[offset:offset + 2])[0]
#             offset += 2
#             logger.debug(f"Standard Version: 0x{standard_version:04x}")
#
#             # Vendor Extension ID (4바이트)
#             vendor_ext_id = struct.unpack('<I', data[offset:offset + 4])[0]
#             offset += 4
#             logger.debug(f"Vendor Extension ID: 0x{vendor_ext_id:08x}")
#
#             # Vendor Extension Version (2바이트)
#             vendor_ext_version = struct.unpack('<H', data[offset:offset + 2])[0]
#             offset += 2
#             logger.debug(f"Vendor Extension Version: 0x{vendor_ext_version:04x}")
#
#             # 벤더 확장 설명 읽기 (PTP String)
#             vendor_desc = ""
#             if offset < len(data):
#                 desc_len = struct.unpack('<B', data[offset:offset + 1])[0]
#                 offset += 1
#                 logger.debug(f"벤더 설명 길이: {desc_len} 문자")
#
#                 if desc_len > 0 and offset + desc_len * 2 <= len(data):
#                     vendor_desc_bytes = data[offset:offset + desc_len * 2]
#                     vendor_desc = vendor_desc_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
#                     offset += desc_len * 2
#                     logger.info(f"벤더 설명: {vendor_desc}")
#
#             # Functional Mode (2바이트)
#             if offset + 2 <= len(data):
#                 functional_mode = struct.unpack('<H', data[offset:offset + 2])[0]
#                 offset += 2
#                 logger.debug(f"Functional Mode: 0x{functional_mode:04x}")
#
#             # 지원되는 동작 코드 읽기 (PTP Array)
#             operations = []
#             if offset + 4 <= len(data):
#                 op_count = struct.unpack('<I', data[offset:offset + 4])[0]
#                 offset += 4
#                 logger.info(f"지원되는 동작 개수: {op_count}")
#
#                 # 동작 코드 읽기
#                 for i in range(op_count):
#                     if offset + 2 <= len(data):
#                         op_code = struct.unpack('<H', data[offset:offset + 2])[0]
#                         operations.append(op_code)
#                         offset += 2
#
#                         # 중요한 동작 코드 로깅
#                         if op_code in [self.PTP_OC_GetDeviceInfo, self.PTP_OC_OpenSession,
#                                        self.PTP_OC_CloseSession, self.NIKON_OC_PIN_AUTH,
#                                        self.NIKON_OC_UNKNOWN_944C, self.NIKON_OC_UNKNOWN_952A]:
#                             op_name = self._get_operation_name(op_code)
#                             logger.debug(f"중요 동작 발견: {op_name} (0x{op_code:04x})")
#
#             # 동작 코드 목록 출력
#             if operations:
#                 operations_preview = [f'0x{op:04x}' for op in operations[:10]]
#                 logger.info(f"지원 동작 (처음 10개): {', '.join(operations_preview)}")
#                 if len(operations) > 10:
#                     logger.info(f"... 및 {len(operations) - 10}개 더")
#
#             # 이벤트 코드 읽기 (PTP Array)
#             events = []
#             if offset + 4 <= len(data):
#                 event_count = struct.unpack('<I', data[offset:offset + 4])[0]
#                 offset += 4
#                 logger.debug(f"지원되는 이벤트 개수: {event_count}")
#
#                 for i in range(event_count):
#                     if offset + 2 <= len(data):
#                         event_code = struct.unpack('<H', data[offset:offset + 2])[0]
#                         events.append(event_code)
#                         offset += 2
#
#             # 장치 속성 코드 읽기 (PTP Array)
#             properties = []
#             if offset + 4 <= len(data):
#                 prop_count = struct.unpack('<I', data[offset:offset + 4])[0]
#                 offset += 4
#                 logger.debug(f"지원되는 장치 속성 개수: {prop_count}")
#
#                 for i in range(prop_count):
#                     if offset + 2 <= len(data):
#                         prop_code = struct.unpack('<H', data[offset:offset + 2])[0]
#                         properties.append(prop_code)
#                         offset += 2
#
#             # 캡처 형식 읽기 (PTP Array)
#             capture_formats = []
#             if offset + 4 <= len(data):
#                 format_count = struct.unpack('<I', data[offset:offset + 4])[0]
#                 offset += 4
#                 logger.debug(f"지원되는 캡처 형식 개수: {format_count}")
#
#                 for i in range(format_count):
#                     if offset + 2 <= len(data):
#                         format_code = struct.unpack('<H', data[offset:offset + 2])[0]
#                         capture_formats.append(format_code)
#                         offset += 2
#
#             # 이미지 형식 읽기 (PTP Array)
#             image_formats = []
#             if offset + 4 <= len(data):
#                 img_format_count = struct.unpack('<I', data[offset:offset + 4])[0]
#                 offset += 4
#                 logger.debug(f"지원되는 이미지 형식 개수: {img_format_count}")
#
#                 for i in range(img_format_count):
#                     if offset + 2 <= len(data):
#                         img_format_code = struct.unpack('<H', data[offset:offset + 2])[0]
#                         image_formats.append(img_format_code)
#                         offset += 2
#
#             # 제조사 이름 읽기 (PTP String)
#             manufacturer = ""
#             if offset < len(data):
#                 mfg_len = struct.unpack('<B', data[offset:offset + 1])[0]
#                 offset += 1
#                 if mfg_len > 0 and offset + mfg_len * 2 <= len(data):
#                     mfg_bytes = data[offset:offset + mfg_len * 2]
#                     manufacturer = mfg_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
#                     offset += mfg_len * 2
#                     logger.info(f"제조사: {manufacturer}")
#
#             # 모델명 읽기 (PTP String)
#             model = ""
#             if offset < len(data):
#                 model_len = struct.unpack('<B', data[offset:offset + 1])[0]
#                 offset += 1
#                 if model_len > 0 and offset + model_len * 2 <= len(data):
#                     model_bytes = data[offset:offset + model_len * 2]
#                     model = model_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
#                     offset += model_len * 2
#                     logger.info(f"모델명: {model}")
#
#             # 장치 버전 읽기 (PTP String)
#             device_version = ""
#             if offset < len(data):
#                 ver_len = struct.unpack('<B', data[offset:offset + 1])[0]
#                 offset += 1
#                 if ver_len > 0 and offset + ver_len * 2 <= len(data):
#                     ver_bytes = data[offset:offset + ver_len * 2]
#                     device_version = ver_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
#                     offset += ver_len * 2
#                     logger.info(f"장치 버전: {device_version}")
#
#             # 시리얼 번호 읽기 (PTP String)
#             serial_number = ""
#             if offset < len(data):
#                 serial_len = struct.unpack('<B', data[offset:offset + 1])[0]
#                 offset += 1
#                 if serial_len > 0 and offset + serial_len * 2 <= len(data):
#                     serial_bytes = data[offset:offset + serial_len * 2]
#                     serial_number = serial_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
#                     offset += serial_len * 2
#                     logger.info(f"시리얼 번호: {serial_number}")
#
#             logger.info(f"총 {len(operations)}개의 동작 코드 지원")
#             logger.info(f"니콘 전용 동작 지원 여부:")
#             logger.info(f"  - PIN 인증 (0x935a): {'예' if self.NIKON_OC_PIN_AUTH in operations else '아니오'}")
#             logger.info(f"  - Unknown_944C: {'예' if self.NIKON_OC_UNKNOWN_944C in operations else '아니오'}")
#             logger.info(f"  - Unknown_952A: {'예' if self.NIKON_OC_UNKNOWN_952A in operations else '아니오'}")
#
#             return {
#                 'standard_version': standard_version,
#                 'vendor_extension_id': vendor_ext_id,
#                 'vendor_description': vendor_desc,
#                 'manufacturer': manufacturer,
#                 'model': model,
#                 'device_version': device_version,
#                 'serial_number': serial_number,
#                 'operations': operations,
#                 'events': events,
#                 'properties': properties,
#                 'capture_formats': capture_formats,
#                 'image_formats': image_formats,
#                 'operation_count': len(operations),
#                 'supports_pin_auth': self.NIKON_OC_PIN_AUTH in operations,
#                 'supports_944c': self.NIKON_OC_UNKNOWN_944C in operations,
#                 'supports_952a': self.NIKON_OC_UNKNOWN_952A in operations
#             }
#
#         except Exception as e:
#             logger.error(f"장치 정보 파싱 중 오류: {e}")
#             logger.debug("파싱 오류 상세:", exc_info=True)
#             return {
#                 'vendor_description': vendor_desc if 'vendor_desc' in locals() else '',
#                 'operations': operations if 'operations' in locals() else [],
#                 'operation_count': len(operations) if 'operations' in locals() else 0,
#                 'supports_pin_auth': False,
#                 'supports_944c': False,
#                 'supports_952a': False
#             }
#
#     def open_session(self) -> bool:
#         """PTP 세션을 여는 메서드"""
#         logger.info("PTP 세션 열기 시작")
#         logger.info("=" * 50)
#         logger.info(f"세션 ID: {self.session_id}")
#
#         # 공식앱과 동일하게 OpenSession도 Transaction ID 0 사용
#         original_transaction_id = self.transaction_id
#         self.transaction_id = 0  # 공식앱 패턴에 맞춰 0으로 설정
#
#         response_code, _ = self._send_ptp_command(self.PTP_OC_OpenSession, [self.session_id])
#
#         # Transaction ID를 1로 설정 (다음 명령부터 1 시작)
#         self.transaction_id = 1
#
#         if response_code == self.PTP_RC_OK:
#             logger.info("PTP 세션 열기 성공")
#             return True
#         else:
#             logger.error(f"PTP 세션 열기 실패: 응답 코드 0x{response_code:04x}")
#             return False
#
#     def authenticate_pin(self, pin_code: str) -> bool:
#         """4자리 PIN 코드로 인증하는 메서드"""
#         logger.info("PIN 인증 시작")
#         logger.info("=" * 50)
#         logger.info(f"PIN 코드: {pin_code}")
#
#         # PIN을 정수로 변환
#         try:
#             pin_int = int(pin_code)
#             if not (0 <= pin_int <= 9999):
#                 logger.error("PIN 코드는 0000-9999 범위여야 합니다")
#                 return False
#             logger.debug(f"PIN 정수값: {pin_int}")
#         except ValueError:
#             logger.error("잘못된 PIN 코드 형식")
#             return False
#
#         # 니콘 PIN 인증 명령 전송
#         logger.info("PIN 인증 명령 전송 중...")
#         response_code, _ = self._send_ptp_command(self.NIKON_OC_PIN_AUTH, [pin_int])
#
#         if response_code == self.PTP_RC_OK:
#             logger.info("PIN 인증 명령 전송 성공")
#
#             # 장치 정보 변경 이벤트 대기
#             logger.info("장치 정보 변경 이벤트 대기 중...")
#             logger.info("(카메라에서 인증 완료 신호를 기다리는 중...)")
#
#             # 이벤트 수신 대기 (타임아웃 10초)
#             if self.event_received.wait(timeout=10):
#                 logger.info("인증 성공! 모든 기능을 사용할 수 있습니다.")
#                 return True
#             else:
#                 logger.error("인증 응답 대기 타임아웃 - PIN 코드를 확인하세요")
#                 return False
#         else:
#             logger.error(f"PIN 인증 명령 실패: 응답 코드 0x{response_code:04x}")
#             return False
#
#     def get_storage_ids(self) -> list:
#         """저장소 ID를 가져오는 메서드"""
#         logger.info("저장소 ID 요청 시작")
#         logger.info("=" * 50)
#
#         response_code, data = self._send_ptp_command(self.PTP_OC_GetStorageIDs)
#
#         if response_code == self.PTP_RC_OK and data:
#             logger.info("저장소 ID 수신 성공")
#             return self._parse_storage_ids(data)
#         else:
#             logger.error(f"저장소 ID 가져오기 실패: 응답 코드 0x{response_code:04x}")
#             return []
#
#     def _parse_storage_ids(self, data: bytes) -> list:
#         """저장소 ID 데이터를 파싱하는 메서드"""
#         logger.info("저장소 ID 파싱 시작")
#         logger.debug(f"파싱할 데이터 크기: {len(data)} 바이트")
#         logger.debug(f"저장소 ID 데이터: {data.hex()}")
#
#         if len(data) < 4:
#             logger.error("저장소 ID 데이터가 너무 짧음")
#             return []
#
#         try:
#             # PTP 배열 형태: [개수(4바이트)] [ID1(4바이트)] [ID2(4바이트)] ...
#             storage_count = struct.unpack('<I', data[0:4])[0]
#             logger.info(f"저장소 개수: {storage_count}")
#
#             storage_ids = []
#             offset = 4
#
#             for i in range(storage_count):
#                 if offset + 4 <= len(data):
#                     storage_id = struct.unpack('<I', data[offset:offset + 4])[0]
#                     storage_ids.append(storage_id)
#                     logger.debug(f"저장소 ID {i}: 0x{storage_id:08x}")
#                     offset += 4
#                 else:
#                     logger.warning(f"저장소 ID {i} 데이터 부족")
#                     break
#
#             logger.info(f"총 {len(storage_ids)}개의 저장소 ID 파싱 완료")
#             return storage_ids
#
#         except Exception as e:
#             logger.error(f"저장소 ID 파싱 중 오류: {e}")
#             return []
#
#     def close_session(self) -> bool:
#         """PTP 세션을 닫는 메서드"""
#         logger.info("PTP 세션 닫기 시작")
#         logger.info("=" * 50)
#         logger.info(f"세션 ID: {self.session_id}")
#
#         response_code, _ = self._send_ptp_command(self.PTP_OC_CloseSession)
#
#         if response_code == self.PTP_RC_OK:
#             logger.info("PTP 세션 닫기 성공")
#             return True
#         else:
#             logger.error(f"PTP 세션 닫기 실패: 응답 코드 0x{response_code:04x}")
#             return False
#
#     def disconnect(self):
#         """카메라와의 연결을 끊는 메서드"""
#         logger.info("카메라 연결 해제 시작")
#
#         # 명령 소켓 닫기
#         if self.command_socket:
#             try:
#                 self.command_socket.close()
#                 logger.info("명령 소켓 닫기 완료")
#             except Exception as e:
#                 logger.warning(f"명령 소켓 닫기 중 오류: {e}")
#             finally:
#                 self.command_socket = None
#
#         # 이벤트 소켓 닫기
#         if self.event_socket:
#             try:
#                 self.event_socket.close()
#                 logger.info("이벤트 소켓 닫기 완료")
#             except Exception as e:
#                 logger.warning(f"이벤트 소켓 닫기 중 오류: {e}")
#             finally:
#                 self.event_socket = None
#
#         # 이벤트 스레드 종료 대기
#         if self.event_thread and self.event_thread.is_alive():
#             logger.info("이벤트 스레드 종료 대기 중...")
#             self.event_thread.join(timeout=2)
#             if self.event_thread.is_alive():
#                 logger.warning("이벤트 스레드가 정상적으로 종료되지 않았습니다")
#             else:
#                 logger.info("이벤트 스레드 종료 완료")
#
#         logger.info("카메라 연결 해제 완료")
#
#     def _send_ptp_command_935a(self) -> Tuple[int, bytes]:
#         """Frame 45와 동일한 0x935a 오퍼레이션 전송 (연결 승인 요청)"""
#         logger.info("0x935a 연결 승인 요청 전송 중...")
#
#         # Frame 45 분석 결과: 22바이트 패킷, Transaction ID 2
#         # Hex: 16 00 00 00 06 00 00 00 01 00 00 00 5a 93 02 00 00 00 01 20 00 00
#
#         # Transaction ID 2로 고정 (Frame 45와 동일)
#         transaction_id_to_use = 2
#
#         # Frame 45와 정확히 동일한 22바이트 패킷 구성
#         packet_length = 22
#         packet = struct.pack('<II', packet_length, self.PTPIP_CMD_REQUEST)  # 길이 + 타입
#         packet += struct.pack('<IHI', 1, 0x935a,
#                               transaction_id_to_use)  # data_phase=1, op_code=0x935a, transaction_id=2
#
#         # Frame 45에서 관찰된 매개변수: 01 20 00 00 (0x2001 = 8193 = PTP_RC_OK?)
#         packet += struct.pack('<I', 0x2001)  # 매개변수
#
#         logger.debug(f"0x935a 패킷 길이: {len(packet)} 바이트")
#         logger.debug(f"0x935a 패킷 데이터: {packet.hex()}")
#
#         # Frame 45와 동일한 패킷인지 확인
#         expected_packet = "1600000006000000010000005a93020000000120000"
#         actual_hex = packet.hex()
#         logger.debug(f"예상 패킷: {expected_packet}")
#         logger.debug(f"실제 패킷: {actual_hex}")
#
#         if actual_hex.startswith("1600000006000000010000005a9302000000"):
#             logger.info("✅ Frame 45와 동일한 0x935a 패킷 구성!")
#         else:
#             logger.warning("⚠️ Frame 45와 다른 패킷 구성")
#
#         # 패킷 전송
#         try:
#             bytes_sent = self.command_socket.send(packet)
#             logger.info(f"📤 0x935a 패킷 전송 완료: {bytes_sent}/{len(packet)} 바이트")
#         except Exception as e:
#             logger.error(f"0x935a 패킷 전송 실패: {e}")
#             return 0, b''
#
#         # 응답 수신 (Frame 46과 동일한 응답 예상)
#         response_data = b''
#         response_code = 0
#
#         try:
#             logger.info("📥 0x935a 응답 수신 대기 중...")
#             self.command_socket.settimeout(10)
#
#             raw_response = self.command_socket.recv(4096)
#             logger.info(f"📥 0x935a 응답 수신: {len(raw_response)} 바이트")
#             logger.debug(f"📥 응답 데이터: {raw_response.hex()}")
#
#             if len(raw_response) < 8:
#                 logger.error("0x935a 응답 데이터가 너무 짧음")
#                 return 0, b''
#
#             # PTP/IP 헤더 파싱
#             length, packet_type = struct.unpack('<II', raw_response[:8])
#             logger.debug(f"📥 패킷 길이: {length}, 타입: {packet_type}")
#
#             if packet_type == self.PTPIP_CMD_RESPONSE:
#                 # Frame 46과 동일한 응답 패킷
#                 if length >= 14:
#                     response_code = struct.unpack('<H', raw_response[8:10])[0]
#                     transaction_id = struct.unpack('<I', raw_response[10:14])[0]
#                     logger.info(f"📥 0x935a 응답: 코드=0x{response_code:04x}, 트랜잭션={transaction_id}")
#
#                     # Frame 46 예상: OK (0x2001), Transaction ID: 2
#                     if response_code == self.PTP_RC_OK and transaction_id == 2:
#                         logger.info("✅ Frame 46과 동일한 성공 응답!")
#
#             elif packet_type == self.PTPIP_START_DATA_PACKET:
#                 # 데이터가 있는 응답인 경우
#                 logger.debug("📥 0x935a Start Data Packet 수신")
#                 response_data, response_code, _ = self._parse_multiple_ptpip_packets(raw_response)
#
#         except socket.timeout:
#             logger.error("❌ 0x935a 응답 수신 타임아웃")
#         except Exception as e:
#             logger.error(f"❌ 0x935a 응답 수신 중 오류: {e}")
#             logger.debug("0x935a 응답 수신 오류 상세:", exc_info=True)
#
#         # 결과 로깅
#         logger.info(f"📥 0x935a 연결 승인 요청 완료")
#         logger.info(f"   응답 코드: 0x{response_code:04x}")
#         logger.info(f"   트랜잭션ID: 2")
#
#         if response_code == self.PTP_RC_OK:
#             logger.info("✅ 0x935a 연결 승인 성공")
#         else:
#             logger.warning(f"❌ 0x935a 연결 승인 실패: 응답 코드 0x{response_code:04x}")
#
#         return response_code, response_data
#
#
# def main():
#     """PTP 클라이언트를 테스트하는 메인 함수"""
#     logger.info("니콘 PTP/IP 클라이언트 시작")
#     logger.info("=" * 60)
#
#     # 카메라 설정
#     camera_ip = "192.168.147.75"  # 카메라 LCD에서 확인된 실제 IP로 변경
#     logger.info(f"카메라 IP 주소: {camera_ip}")
#
#     # === Phase 1: 초기 연결 및 승인 요청 (Frame 1~47) ===
#     logger.info("\n=== Phase 1: 초기 연결 및 승인 요청 (Frame 1~47) ===")
#
#     # PTP 클라이언트 생성
#     client = PTPIPClient(camera_ip)
#
#     try:
#         # 1단계: 카메라 연결
#         logger.info("1단계: 카메라 연결 시도 중...")
#         if not client.connect():
#             logger.error("카메라 연결 실패")
#             return
#
#         # 2단계: 초기 장치 정보 가져오기 (Frame 29와 동일)
#         logger.info("\n2단계: GetDeviceInfo (Frame 29와 동일)")
#         logger.info("=" * 60)
#         device_info = client.get_device_info()
#         if device_info:
#             logger.info(f"인증 전 사용 가능한 동작: {device_info['operation_count']}개")
#             logger.info(f"제조사: {device_info.get('manufacturer', 'Unknown')}")
#             logger.info(f"모델명: {device_info.get('model', 'Unknown')}")
#         else:
#             logger.warning("초기 장치 정보 가져오기 실패")
#
#         # 3단계: 세션 열기 (Frame 37와 동일)
#         logger.info("\n3단계: OpenSession (Frame 37와 동일)")
#         logger.info("=" * 60)
#         if not client.open_session():
#             logger.error("세션 열기 실패")
#             return
#
#         # 4단계: 니콘 전용 오퍼레이션 0x952b (Frame 40-43과 동일)")
#         logger.info("\n4단계: 니콘 전용 오퍼레이션 0x952b (Frame 40-43과 동일)")
#         logger.info("=" * 60)
#         logger.info("0x952b 오퍼레이션 실행 중...")
#
#         response_code, data = client._send_ptp_command(0x952b)
#         if response_code == client.PTP_RC_OK:
#             logger.info("✅ 0x952b 오퍼레이션 성공!")
#             if data:
#                 logger.info(f"카메라에서 수신한 데이터: {len(data)} 바이트")
#                 logger.info(f"수신 데이터 내용: {data.hex()}")
#             else:
#                 logger.warning("데이터를 수신하지 못했습니다")
#         else:
#             logger.warning(f"0x952b 오퍼레이션 실패: 응답 코드 0x{response_code:04x}")
#             return
#
#         # 5단계: 니콘 전용 오퍼레이션 0x935a (Frame 45와 동일) - 연결 승인 요청
#         logger.info("\n5단계: 니콘 전용 오퍼레이션 0x935a (Frame 45와 동일)")
#         logger.info("=" * 60)
#         logger.info("연결 승인 요청 0x935a 실행 중...")
#
#         response_code, data = client._send_ptp_command_935a()
#         if response_code == client.PTP_RC_OK:
#             logger.info("✅ 0x935a 연결 승인 성공!")
#             logger.info("카메라가 연결을 승인했습니다 - 기존 연결이 종료됩니다")
#         else:
#             logger.warning(f"0x935a 연결 승인 실패: 응답 코드 0x{response_code:04x}")
#             return
#
#         # Phase 1 완료 - 기존 연결 정리
#         logger.info("\n=== Phase 1 완료: 기존 연결 정리 ===")
#         client.disconnect()
#
#         # 카메라가 내부적으로 상태를 변경하는 시간 대기
#         logger.info("카메라 내부 처리 대기 중... (5초)")
#         time.sleep(5)
#
#     except Exception as e:
#         logger.error(f"Phase 1 중 오류 발생: {e}")
#         client.disconnect()
#         return
#
#     # === Phase 2: 새로운 인증된 연결 (Frame 68~) ===
#     logger.info("\n=== Phase 2: 새로운 인증된 연결 (Frame 68~) ===")
#
#     # 새로운 클라이언트 인스턴스로 재연결
#     logger.info("새로운 인증된 연결 시작...")
#     authenticated_client = PTPIPClient(camera_ip)
#
#     try:
#         # 6단계: 인증된 연결 설정
#         logger.info("\n6단계: 인증된 연결 설정")
#         logger.info("=" * 60)
#         if not authenticated_client.connect():
#             logger.error("인증된 연결 실패")
#             return
#
#         logger.info("✅ 새로운 인증된 연결 성공!")
#
#         # 7단계: 인증된 상태에서 장치 정보 확인
#         logger.info("\n7단계: 인증된 상태 장치 정보 확인 (Frame 68+ 상태)")
#         logger.info("=" * 60)
#         device_info = authenticated_client.get_device_info()
#         if device_info:
#             logger.info(f"인증 후 사용 가능한 동작: {device_info['operation_count']}개")
#             logger.info(f"니콘 전용 동작 지원 여부:")
#             logger.info(f"  - 0x944c: {'예' if device_info['supports_944c'] else '아니오'}")
#             logger.info(f"  - 0x952a: {'예' if device_info['supports_952a'] else '아니오'}")
#             if device_info.get('supports_944c'):
#                 logger.info("🎉 0x944c 사용 가능! 모든 기능이 활성화되었습니다.")
#         else:
#             logger.warning("인증된 장치 정보 가져오기 실패")
#
#         # 8단계: 인증된 세션 열기
#         logger.info("\n8단계: 인증된 세션 열기")
#         logger.info("=" * 60)
#         if not authenticated_client.open_session():
#             logger.warning("인증된 세션 열기 실패")
#         else:
#             logger.info("✅ 인증된 세션 열기 성공!")
#
#         # 9단계: 저장소 ID 확인 (인증된 상태에서만 가능)
#         logger.info("\n9단계: 저장소 ID 확인 (인증된 상태)")
#         logger.info("=" * 60)
#         storage_ids = authenticated_client.get_storage_ids()
#         if storage_ids:
#             logger.info(f"✅ 저장소 ID 획득 성공: {len(storage_ids)}개")
#             for i, storage_id in enumerate(storage_ids):
#                 logger.info(f"  저장소 {i}: 0x{storage_id:08x}")
#         else:
#             logger.warning("저장소 ID 가져오기 실패")
#
#         # # 10단계: 인증된 세션 닫기
#         # logger.info("\n10단계: 인증된 세션 닫기")
#         # logger.info("=" * 60)
#         # if not authenticated_client.close_session():
#         #     logger.warning("인증된 세션 닫기 실패")
#         # else:
#         #     logger.info("✅ 인증된 세션 닫기 성공!")
#
#         logger.info("\n🎉 모든 인증 과정이 성공적으로 완료되었습니다! 🎉")
#         logger.info("이제 카메라의 모든 기능을 사용할 수 있습니다.")
#
#         # 연결을 유지한 채로 대기 (공식 앱처럼)
#         logger.info("\n=== 연결 유지 중 ===")
#         logger.info("카메라와의 인증된 연결이 활성 상태입니다.")
#         logger.info("Ctrl+C를 눌러 프로그램을 종료하세요.")
#
#         # 무한 대기 (공식 앱처럼 연결 유지)
#         try:
#             while True:
#                 time.sleep(10)  # 10초마다 체크
#                 # 연결 상태 확인 (선택적)
#                 if authenticated_client.command_socket and authenticated_client.command_socket.fileno() != -1:
#                     logger.debug("연결 상태: 정상")
#                 else:
#                     logger.warning("연결이 끊어졌습니다")
#                     break
#         except KeyboardInterrupt:
#             logger.info("\n사용자가 연결 종료를 요청했습니다")
#
#     except KeyboardInterrupt:
#         logger.info("\n사용자가 프로그램을 중단했습니다")
#     except Exception as e:
#         logger.error(f"Phase 2 중 오류 발생: {e}")
#         logger.debug("오류 상세 정보:", exc_info=True)
#     finally:
#         # 정리 작업 (사용자가 명시적으로 종료할 때만)
#         logger.info("정리 작업 시작...")
#         if 'authenticated_client' in locals():
#             logger.info("인증된 연결 종료 중...")
#             authenticated_client.disconnect()
#         logger.info("프로그램 종료")
#
# if __name__ == "__main__":
#     main()