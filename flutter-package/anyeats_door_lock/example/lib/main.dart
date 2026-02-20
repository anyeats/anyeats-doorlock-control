import 'package:flutter/material.dart';
import 'package:anyeats_door_lock/anyeats_door_lock.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Door Lock Control',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const DoorLockPage(),
    );
  }
}

class DoorLockPage extends StatefulWidget {
  const DoorLockPage({super.key});

  @override
  State<DoorLockPage> createState() => _DoorLockPageState();
}

class _DoorLockPageState extends State<DoorLockPage> {
  final _controller = DoorLockController();
  final _hexController = TextEditingController();

  List<String> _ports = [];
  String? _selectedPort;
  bool _connected = false;
  final List<String> _logs = [];

  @override
  void initState() {
    super.initState();
    _refreshPorts();
  }

  @override
  void dispose() {
    _controller.disconnect();
    _hexController.dispose();
    super.dispose();
  }

  void _refreshPorts() {
    setState(() {
      _ports = DoorLockController.getAvailablePorts();
      if (_ports.isNotEmpty && _selectedPort == null) {
        _selectedPort = _ports.first;
      }
    });
  }

  void _log(String message) {
    setState(() {
      _logs.insert(0, '[${DateTime.now().toString().substring(11, 19)}] $message');
      if (_logs.length > 50) _logs.removeLast();
    });
  }

  void _connect() {
    if (_selectedPort == null) return;
    final ok = _controller.connect(port: _selectedPort);
    setState(() => _connected = ok);
    _log(ok ? '연결 성공: $_selectedPort' : '연결 실패: $_selectedPort');
  }

  void _disconnect() {
    _controller.disconnect();
    setState(() => _connected = false);
    _log('연결 해제');
  }

  Future<void> _open() async {
    final ok = await _controller.openLock();
    _log(ok ? 'Open 명령 전송 (10 02 01 1B 31 FF 10 03)' : 'Open 실패');
  }

  Future<void> _close() async {
    final ok = await _controller.closeLock();
    _log(ok ? 'Close 명령 전송 (10 02 01 1B 30 FF 10 03)' : 'Close 실패');
  }

  Future<void> _sendRaw() async {
    final hex = _hexController.text.trim();
    if (hex.isEmpty) return;
    final ok = await _controller.sendRaw(hex);
    _log(ok ? 'Raw 전송: $hex' : 'Raw 전송 실패');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Door Lock Control')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 포트 선택 + 연결
            Row(
              children: [
                Expanded(
                  child: DropdownButton<String>(
                    value: _selectedPort,
                    isExpanded: true,
                    hint: const Text('COM 포트 선택'),
                    items: _ports
                        .map((p) => DropdownMenuItem(value: p, child: Text(p)))
                        .toList(),
                    onChanged: (v) => setState(() => _selectedPort = v),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _refreshPorts,
                  icon: const Icon(Icons.refresh),
                  tooltip: '포트 새로고침',
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _connected ? _disconnect : _connect,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _connected ? Colors.red : Colors.green,
                    foregroundColor: Colors.white,
                  ),
                  child: Text(_connected ? '연결 해제' : '연결'),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Open / Close 버튼
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 60,
                    child: ElevatedButton.icon(
                      onPressed: _connected ? _open : null,
                      icon: const Icon(Icons.lock_open, size: 28),
                      label: const Text('Open', style: TextStyle(fontSize: 18)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: SizedBox(
                    height: 60,
                    child: ElevatedButton.icon(
                      onPressed: _connected ? _close : null,
                      icon: const Icon(Icons.lock, size: 28),
                      label:
                          const Text('Close', style: TextStyle(fontSize: 18)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.orange,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Raw Hex 전송
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _hexController,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      hintText: '예: 10 02 01 1B 31 FF 10 03',
                      labelText: 'Raw Hex',
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _connected ? _sendRaw : null,
                  child: const Text('전송'),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // 로그
            const Text('Log', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black87,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: ListView.builder(
                  itemCount: _logs.length,
                  itemBuilder: (_, i) => Text(
                    _logs[i],
                    style: const TextStyle(
                      color: Colors.greenAccent,
                      fontFamily: 'monospace',
                      fontSize: 12,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
