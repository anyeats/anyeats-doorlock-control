"""
Door Lock Control Web Application
Flask 기반 웹 인터페이스로 잠금장치 제어
"""
from flask import Flask, render_template, jsonify, request
from door_lock_controller import DoorLockController
import traceback

app = Flask(__name__)

# 전역 컨트롤러 인스턴스
controller = None

def get_controller():
    """컨트롤러 인스턴스 가져오기"""
    global controller
    if controller is None:
        port = request.args.get('port', 'COM2')
        controller = DoorLockController(port=port)
    return controller


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/open', methods=['POST'])
def open_lock():
    """잠금장치 열기 API"""
    try:
        ctrl = get_controller()

        # 상세 로그 출력
        print(f"\n{'='*60}")
        print(f"[OPEN] 명령 전송 시작")
        print(f"포트: {ctrl.port}, Baud: {ctrl.baudrate}")
        print(f"RTS/CTS: 활성화, CR 추가: {ctrl.append_cr}")
        print(f"{'='*60}\n")

        success = ctrl.open_lock()

        command_hex = '01 00 00 00' + (' 0D' if ctrl.append_cr else '')

        if success:
            return jsonify({
                'success': True,
                'message': '잠금장치를 열었습니다.',
                'command': command_hex,
                'details': {
                    'port': ctrl.port,
                    'rtscts': True,
                    'append_cr': ctrl.append_cr
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '명령 전송에 실패했습니다.'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/close', methods=['POST'])
def close_lock():
    """잠금장치 닫기 API"""
    try:
        ctrl = get_controller()

        # 상세 로그 출력
        print(f"\n{'='*60}")
        print(f"[CLOSE] 명령 전송 시작")
        print(f"포트: {ctrl.port}, Baud: {ctrl.baudrate}")
        print(f"RTS/CTS: 활성화, CR 추가: {ctrl.append_cr}")
        print(f"{'='*60}\n")

        success = ctrl.close_lock()

        command_hex = '00 00 00 00' + (' 0D' if ctrl.append_cr else '')

        if success:
            return jsonify({
                'success': True,
                'message': '잠금장치를 닫았습니다.',
                'command': command_hex,
                'details': {
                    'port': ctrl.port,
                    'rtscts': True,
                    'append_cr': ctrl.append_cr
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '명령 전송에 실패했습니다.'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/status', methods=['GET'])
def read_status():
    """잠금장치 상태 읽기 API"""
    try:
        ctrl = get_controller()
        status = ctrl.read_status()

        if status:
            return jsonify({
                'success': True,
                'status': status['status'],
                'status_code': status['status_code'],
                'raw_data': status['raw_data'],
                'message': f"현재 상태: {'열림' if status['status'] == 'open' else '닫힘'}"
            })
        else:
            return jsonify({
                'success': False,
                'message': '상태 읽기에 실패했습니다.'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/check-id', methods=['GET'])
def check_id():
    """장치 ID 확인 API"""
    try:
        ctrl = get_controller()
        device_id = ctrl.check_id()

        if device_id is not None:
            return jsonify({
                'success': True,
                'device_id': device_id,
                'message': f'장치 ID: {device_id}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'ID 확인에 실패했습니다.'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/connection-test', methods=['GET'])
def connection_test():
    """연결 테스트 API"""
    try:
        ctrl = get_controller()
        success = ctrl.connect()

        if success:
            return jsonify({
                'success': True,
                'message': f'포트 {ctrl.port}에 성공적으로 연결되었습니다.',
                'port': ctrl.port,
                'baudrate': ctrl.baudrate
            })
        else:
            return jsonify({
                'success': False,
                'message': '연결에 실패했습니다.'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/set-port', methods=['POST'])
def set_port():
    """COM 포트 설정 API"""
    try:
        global controller
        data = request.get_json()
        port = data.get('port', 'COM2')

        # 기존 연결 해제
        if controller:
            controller.disconnect()

        # 새 컨트롤러 생성
        controller = DoorLockController(port=port)

        return jsonify({
            'success': True,
            'message': f'포트가 {port}로 설정되었습니다.',
            'port': port
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}'
        }), 500


@app.route('/api/toggle-cr', methods=['POST'])
def toggle_cr():
    """CR 추가 옵션 토글 API"""
    try:
        global controller
        data = request.get_json()
        append_cr = data.get('append_cr', True)

        # 기존 연결 해제
        if controller:
            port = controller.port
            controller.disconnect()
        else:
            port = 'COM2'

        # CR 옵션으로 새 컨트롤러 생성
        controller = DoorLockController(port=port, append_cr=append_cr)

        return jsonify({
            'success': True,
            'message': f'CR 추가: {"활성화" if append_cr else "비활성화"}',
            'append_cr': append_cr
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}'
        }), 500


@app.route('/api/send-raw', methods=['POST'])
def send_raw():
    """Raw hex 전송 API (프로토콜 실험용)"""
    try:
        ctrl = get_controller()
        data = request.get_json()
        hex_string = data.get('hex', '')

        if not hex_string:
            return jsonify({
                'success': False,
                'message': 'hex 값을 입력해주세요.'
            }), 400

        print(f"\n{'='*60}")
        print(f"[RAW] Hex 전송: {hex_string}")
        print(f"포트: {ctrl.port}, Baud: {ctrl.baudrate}")
        print(f"{'='*60}\n")

        success = ctrl.send_raw(hex_string)

        if success:
            return jsonify({
                'success': True,
                'message': f'전송 완료: {hex_string}',
                'hex': hex_string
            })
        else:
            return jsonify({
                'success': False,
                'message': '전송 실패'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/get-settings', methods=['GET'])
def get_settings():
    """현재 설정 조회 API"""
    try:
        ctrl = get_controller()

        return jsonify({
            'success': True,
            'settings': {
                'port': ctrl.port,
                'baudrate': ctrl.baudrate,
                'append_cr': ctrl.append_cr,
                'rtscts': True
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Door Lock Control Web Server")
    print("=" * 60)
    print("서버 주소: http://localhost:5000")
    print("=" * 60)

    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        if controller:
            controller.disconnect()
