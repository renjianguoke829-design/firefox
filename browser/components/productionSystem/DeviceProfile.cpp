#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <unordered_map>

namespace production_system {

struct DeviceKernelParams {
  std::string navigatorPlatform;
  std::string userAgent;
  std::string language;
  std::string hardwareConcurrency;
  std::string deviceMemory;
  std::string screenWidth;
  std::string screenHeight;
  std::string colorDepth;
  std::string timezone;
  std::string canvasNoiseSeed;
  std::string webglRenderer;
  std::string webglVendor;
  std::string fonts;
  std::string batteryApiRandom;
};

class DeviceProfile {
 public:
  static DeviceKernelParams LoadFromEnvironment() {
    const char* profileIdEnv = std::getenv("PROFILE_ID");
    std::string profileId = profileIdEnv ? profileIdEnv : "production";
    std::string path = "browser/profiles/" + profileId + ".json";
    return LoadFromFile(path);
  }

 private:
  static std::string ReadTextFile(const std::string& path) {
    std::ifstream input(path);
    if (!input.good()) {
      return "";
    }
    std::ostringstream ss;
    ss << input.rdbuf();
    return ss.str();
  }

  static std::string FindJsonValue(const std::string& json, const std::string& key) {
    std::string token = "\"" + key + "\"";
    size_t keyPos = json.find(token);
    if (keyPos == std::string::npos) {
      return "";
    }
    size_t colon = json.find(':', keyPos + token.size());
    if (colon == std::string::npos) {
      return "";
    }
    size_t valueStart = json.find_first_not_of(" \n\r\t", colon + 1);
    if (valueStart == std::string::npos) {
      return "";
    }
    if (json[valueStart] == '"') {
      size_t end = json.find('"', valueStart + 1);
      if (end == std::string::npos) {
        return "";
      }
      return json.substr(valueStart + 1, end - valueStart - 1);
    }
    size_t end = json.find_first_of(",}\n\r\t", valueStart);
    if (end == std::string::npos) {
      return json.substr(valueStart);
    }
    return json.substr(valueStart, end - valueStart);
  }

  static DeviceKernelParams LoadFromFile(const std::string& path) {
    const std::string content = ReadTextFile(path);
    DeviceKernelParams params;
    params.navigatorPlatform = FindJsonValue(content, "navigator.platform");
    params.userAgent = FindJsonValue(content, "navigator.userAgent");
    params.language = FindJsonValue(content, "navigator.language");
    params.hardwareConcurrency = FindJsonValue(content, "navigator.hardwareConcurrency");
    params.deviceMemory = FindJsonValue(content, "navigator.deviceMemory");
    params.screenWidth = FindJsonValue(content, "screen.width");
    params.screenHeight = FindJsonValue(content, "screen.height");
    params.colorDepth = FindJsonValue(content, "screen.colorDepth");
    params.timezone = FindJsonValue(content, "timezone");
    params.canvasNoiseSeed = FindJsonValue(content, "canvas.noiseSeed");
    params.webglRenderer = FindJsonValue(content, "webgl.renderer");
    params.webglVendor = FindJsonValue(content, "webgl.vendor");
    params.fonts = FindJsonValue(content, "fonts");
    params.batteryApiRandom = FindJsonValue(content, "battery.random");
    return params;
  }
};

}  // namespace production_system
