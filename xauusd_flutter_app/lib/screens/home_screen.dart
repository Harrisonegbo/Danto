import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import '../services/auth_service.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  WebSocketChannel? _channel;
  final List<String> _signals = [];
  List<dynamic> _backtests = [];

  @override
  void initState() {
    super.initState();
    _connectWebSocket();
    _loadBacktests();
  }

  void _connectWebSocket() {
    // For Android emulator use 10.0.2.2, for real device use your PC LAN IP
    final uri = Uri.parse('ws://10.0.2.2:8000/ws/signals');
    _channel = WebSocketChannel.connect(uri);
    _channel!.stream.listen((message) {
      final data = jsonDecode(message);
      setState(() {
        if (data['type'] == 'signal') {
          final side = data['signal'] == 1
              ? 'LONG'
              : data['signal'] == -1
                  ? 'SHORT'
                  : 'FLAT';
          _signals.insert(
            0,
            '${DateTime.now().toString().substring(11, 19)} → $side | Conf: ${(data['confidence'] * 100).toStringAsFixed(1)}%',
          );
        } else {
          _signals.insert(0, data['msg'] ?? message.toString());
        }
        if (_signals.length > 50) _signals.removeLast();
      });
    }, onError: (e) {
      setState(() {
        _signals.insert(0, 'WebSocket error – check server');
      });
    });
  }

  Future<void> _loadBacktests() async {
    final auth = context.read<AuthService>();
    final api = context.read<ApiService>();
    if (auth.token == null) return;
    final data = await api.getBacktests(auth.token!);
    setState(() => _backtests = data);
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('XAUUSD AI Trader'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => auth.logout(),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Welcome, ${auth.username ?? "User"}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            const Text(
              'Paper-trading mode only • Not financial advice',
              style: TextStyle(color: Colors.redAccent, fontSize: 12),
            ),
            const SizedBox(height: 20),
            const Text('📡 Live Paper Signals', style: TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Expanded(
              flex: 2,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: _signals.isEmpty
                    ? const Text('Waiting for signals...', style: TextStyle(color: Colors.grey))
                    : ListView.builder(
                        itemCount: _signals.length,
                        itemBuilder: (_, i) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Text(_signals[i], style: const TextStyle(fontSize: 13)),
                        ),
                      ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('📈 Saved Backtests', style: TextStyle(fontSize: 16)),
                TextButton(onPressed: _loadBacktests, child: const Text('Refresh')),
              ],
            ),
            Expanded(
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: _backtests.isEmpty
                    ? const Text('No backtests saved yet.', style: TextStyle(color: Colors.grey))
                    : ListView.builder(
                        itemCount: _backtests.length,
                        itemBuilder: (_, i) {
                          final b = _backtests[i];
                          final stats = b['stats'] ?? {};
                          return ListTile(
                            dense: true,
                            title: Text('#${b['id']} – ${b['created_at']?.toString().substring(0, 19) ?? ""}'),
                            subtitle: Text(
                              'Equity: ${stats['final_equity']?.toStringAsFixed(3) ?? "n/a"}×  |  WR: ${((stats['win_rate'] ?? 0) * 100).toStringAsFixed(1)}%',
                            ),
                          );
                        },
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
