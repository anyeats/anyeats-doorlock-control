import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:anyeats_door_lock/anyeats_door_lock.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('getAvailablePorts returns list', (WidgetTester tester) async {
    final ports = DoorLockController.getAvailablePorts();
    expect(ports, isA<List<String>>());
  });
}
