#include "esp_sleep.h"
#include "driver/rtc_io.h"
#include "driver/adc.h"

#include "esp32/ulp.h"
#include "ulp_main.h"
#include "ulptool.h"
#include "common.h"

#include "esp_adc_cal.h"

#include "USB.h"

#if ARDUINO_SERIAL_PORT
#define HWSerial Serial0
#define USBSerial Serial
#else
#define HWSerial Serial
USBCDC USBSerial;
#endif

extern const uint8_t ulp_main_bin_start[] asm("_binary_ulp_main_bin_start");
extern const uint8_t ulp_main_bin_end[]   asm("_binary_ulp_main_bin_end");

static void init_run_ulp(uint32_t usec);
static void usbEventCallback(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data);

esp_adc_cal_characteristics_t *adc_chars = new esp_adc_cal_characteristics_t;

void setup() {
  
#if !ARDUINO_SERIAL_PORT
  USB.enableDFU();
  USB.productName("ESP32S2-USB");
  USB.begin();
  USBSerial.begin();
#endif

  delay(2000);
  USBSerial.println("USBSerial: ULP Light Sleep adc threshold wakeup example");

  delay(100);

  adc1_config_width(ADC_WIDTH_BIT_13);
  adc1_config_channel_atten(ADC1_CHANNEL_4, ADC_ATTEN_DB_0);

  // TODO: apparently this has to be here???
  adc1_get_raw(ADC1_CHANNEL_5);   // read the input pin, 8129 max

  ESP_ERROR_CHECK( esp_sleep_enable_ulp_wakeup() );

  // wake ulp every 10 msec
  init_run_ulp(1000 * 10);
}

void loop() {
  esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();
  USBSerial.printf("Wakeup reason: %d\n", wakeup_reason);

    // check for the ulp is waiting for the main processor to read the adc result
  if (ulp_bool_mutex || wakeup_reason == ESP_SLEEP_WAKEUP_ULP) {
    USBSerial.printf("mutex: %d, counter: %4i | oversample factor: %3i | adc avg: %i\n",
              ulp_bool_mutex,
              ulp_sample_counter & 0xffff,
              adc_oversampling_factor,
              ulp_adc_avg_result & 0xffff
              );
    USBSerial.flush();

      // tell ulp we are done reading result
    ulp_bool_mutex = false;
  }

  // pinMode(ADC1_CHANNEL_8, INPUT);
  // adc1_config_channel_atten(ADC1_CHANNEL_8, ADC_ATTEN_DB_0);
  // double rawPin = adc1_get_raw(ADC1_CHANNEL_8);   // read the input pin, 8129 max

  // light sleep until adc thershold is exceeded
  // TODO: this messes up the raedings
  // esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_ON);
  esp_deep_sleep_start();
}

static void init_run_ulp(uint32_t usec) {
  adc1_ulp_enable();
  adc1_config_channel_atten(ADC1_CHANNEL_4, ADC_ATTEN_DB_0);
  adc1_config_width(ADC_WIDTH_BIT_13); // max 8191
  //rtc_gpio_pullup_dis(GPIO_NUM_15);
  //rtc_gpio_hold_en(GPIO_NUM_15);
  ulp_set_wakeup_period(0, usec);
  esp_err_t err = ulptool_load_binary(0, ulp_main_bin_start, (ulp_main_bin_end - ulp_main_bin_start) / sizeof(uint32_t));
  // all shared ulp variables have to be intialized after ulptool_load_binary for the ulp to see it.
  // Set the high threshold reading you want the ulp to trigger a main processor wakeup.
  // ulp_threshold = 0x40; // 64 decimal

  // 2048
  // ulp_threshold = 0x800;

  // 1024
  // ulp_threshold = 0x400;

  ulp_threshold = 1850;

  err = ulp_run((&ulp_entry - RTC_SLOW_MEM) / sizeof(uint32_t));
  if (err) USBSerial.println("Error Starting ULP Coprocessor");
}
