#include <Arduino.h>

namespace {

constexpr uint8_t X_STEP_PIN = 2;
constexpr uint8_t Y_STEP_PIN = 3;
constexpr uint8_t X_DIR_PIN = 5;
constexpr uint8_t Y_DIR_PIN = 6;
constexpr uint8_t ENABLE_PIN = 8;

constexpr unsigned long DEFAULT_STEP_DELAY_US = 900;
constexpr unsigned long MIN_STEP_DELAY_US = 250;
constexpr unsigned long DEFAULT_PULSE_WIDTH_US = 8;

long x_position_steps = 0;
long y_position_steps = 0;
unsigned long step_delay_us = DEFAULT_STEP_DELAY_US;
bool motors_enabled = true;

String read_line() {
  static String buffer;
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    if (c == '\r') {
      continue;
    }
    if (c == '\n') {
      String out = buffer;
      buffer = "";
      out.trim();
      return out;
    }
    buffer += c;
  }
  return "";
}

bool extract_long_arg(const String &line, char key, long &value) {
  int index = line.indexOf(key);
  if (index < 0) {
    return false;
  }
  int start = index + 1;
  int end = start;
  while (end < line.length() && line.charAt(end) == ' ') {
    ++end;
  }
  start = end;
  while (end < line.length()) {
    char c = line.charAt(end);
    if ((c >= '0' && c <= '9') || c == '-' || c == '+') {
      ++end;
      continue;
    }
    break;
  }
  if (end == start) {
    return false;
  }
  value = line.substring(start, end).toInt();
  return true;
}

bool extract_ulong_arg(const String &line, char key, unsigned long &value) {
  long parsed = 0;
  if (!extract_long_arg(line, key, parsed)) {
    return false;
  }
  if (parsed < 0) {
    return false;
  }
  value = static_cast<unsigned long>(parsed);
  return true;
}

void set_motor_enabled(bool enabled) {
  motors_enabled = enabled;
  digitalWrite(ENABLE_PIN, enabled ? LOW : HIGH);
}

void pulse_pin(uint8_t step_pin) {
  digitalWrite(step_pin, HIGH);
  delayMicroseconds(DEFAULT_PULSE_WIDTH_US);
  digitalWrite(step_pin, LOW);
}

void move_relative(long dx_steps, long dy_steps) {
  if (!motors_enabled) {
    set_motor_enabled(true);
  }

  digitalWrite(X_DIR_PIN, dx_steps >= 0 ? HIGH : LOW);
  digitalWrite(Y_DIR_PIN, dy_steps >= 0 ? HIGH : LOW);

  unsigned long ax = static_cast<unsigned long>(abs(dx_steps));
  unsigned long ay = static_cast<unsigned long>(abs(dy_steps));
  unsigned long total = ax > ay ? ax : ay;
  if (total == 0) {
    return;
  }

  unsigned long x_accum = 0;
  unsigned long y_accum = 0;

  for (unsigned long i = 0; i < total; ++i) {
    x_accum += ax;
    y_accum += ay;

    if (x_accum >= total) {
      pulse_pin(X_STEP_PIN);
      x_accum -= total;
      x_position_steps += (dx_steps >= 0 ? 1 : -1);
    }

    if (y_accum >= total) {
      pulse_pin(Y_STEP_PIN);
      y_accum -= total;
      y_position_steps += (dy_steps >= 0 ? 1 : -1);
    }

    delayMicroseconds(step_delay_us);
  }
}

void print_help() {
  Serial.println(F("Commands:"));
  Serial.println(F("  X<number> Y<number> [F<us>]  relative move in steps"));
  Serial.println(F("  STATUS                      print current step positions"));
  Serial.println(F("  ENABLE                      energize drivers"));
  Serial.println(F("  DISABLE                     de-energize drivers"));
  Serial.println(F("  ZERO                        set current step position to 0,0"));
  Serial.println(F("Examples:"));
  Serial.println(F("  X200"));
  Serial.println(F("  Y-150"));
  Serial.println(F("  X800 Y400 F700"));
}

void print_status() {
  Serial.print(F("X="));
  Serial.print(x_position_steps);
  Serial.print(F(" Y="));
  Serial.print(y_position_steps);
  Serial.print(F(" STEP_DELAY_US="));
  Serial.print(step_delay_us);
  Serial.print(F(" ENABLED="));
  Serial.println(motors_enabled ? F("1") : F("0"));
}

void handle_command(const String &line) {
  if (line.length() == 0) {
    return;
  }

  if (line.equalsIgnoreCase("HELP")) {
    print_help();
    return;
  }
  if (line.equalsIgnoreCase("STATUS")) {
    print_status();
    return;
  }
  if (line.equalsIgnoreCase("ENABLE")) {
    set_motor_enabled(true);
    Serial.println(F("OK ENABLE"));
    return;
  }
  if (line.equalsIgnoreCase("DISABLE")) {
    set_motor_enabled(false);
    Serial.println(F("OK DISABLE"));
    return;
  }
  if (line.equalsIgnoreCase("ZERO")) {
    x_position_steps = 0;
    y_position_steps = 0;
    Serial.println(F("OK ZERO"));
    return;
  }

  long dx = 0;
  long dy = 0;
  unsigned long requested_delay = step_delay_us;
  bool has_x = extract_long_arg(line, 'X', dx) || extract_long_arg(line, 'x', dx);
  bool has_y = extract_long_arg(line, 'Y', dy) || extract_long_arg(line, 'y', dy);
  bool has_f = extract_ulong_arg(line, 'F', requested_delay) || extract_ulong_arg(line, 'f', requested_delay);

  if (!has_x && !has_y) {
    Serial.println(F("ERR unknown command"));
    return;
  }

  if (has_f) {
    if (requested_delay < MIN_STEP_DELAY_US) {
      requested_delay = MIN_STEP_DELAY_US;
    }
    step_delay_us = requested_delay;
  }

  move_relative(dx, dy);
  Serial.println(F("OK MOVE"));
  print_status();
}

}  // namespace

void setup() {
  pinMode(X_STEP_PIN, OUTPUT);
  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(X_DIR_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);

  digitalWrite(X_STEP_PIN, LOW);
  digitalWrite(Y_STEP_PIN, LOW);
  digitalWrite(X_DIR_PIN, LOW);
  digitalWrite(Y_DIR_PIN, LOW);
  set_motor_enabled(true);

  Serial.begin(115200);
  delay(300);
  Serial.println(F("Zeiss Axio XY serial jogger ready"));
  print_help();
}

void loop() {
  String line = read_line();
  if (line.length() > 0) {
    handle_command(line);
  }
}
