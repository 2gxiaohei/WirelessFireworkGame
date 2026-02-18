/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "i2c.h"
#include "usart.h"
#include "gpio.h"


/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
//添加头文件
#include <string.h>  // 提供strlen函数
#include "driver_oled.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
// 全局变量
uint8_t connect_flag = 0;  // 连接标志
uint8_t fire_flag = 0;      // 发射标志
uint8_t esp_connected = 0;  // ESP01S连接状态标志

// 按键中断回调函数
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if(GPIO_Pin == GPIO_PIN_1)  // PB1按下，连接WiFi和服务器
    {
        if(HAL_GPIO_ReadPin(KEY_CONNECT_GPIO_Port, KEY_CONNECT_Pin) == GPIO_PIN_RESET)
        {
            connect_flag = 1;  // 设置连接标志
        }
    }
    else if(GPIO_Pin == GPIO_PIN_11)  // PB11按下，发射烟花
    {
        if(HAL_GPIO_ReadPin(KEY_FIRE_GPIO_Port, KEY_FIRE_Pin) == GPIO_PIN_RESET)
        {
            if(esp_connected)  // 检查是否已连接
            {
                fire_flag = 1;  // 设置发射标志
            }
        }
    }
}

// ESP01S连接函数
void ESP_Connect(void)
{
    // 发送AT指令序列
    char *at_commands[] = {
        "AT\r\n",
        "AT+CWMODE=1\r\n",
        "AT+CWJAP=\"2GXIAOHEI\",\"123456A#\"\r\n",
        "AT+CIPSTART=\"TCP\",\"192.168.69.185\",8888\r\n"
    };
    
    for(int i = 0; i < 4; i++)
    {
        HAL_UART_Transmit(&huart1, (uint8_t*)at_commands[i], strlen(at_commands[i]), 1000);
        HAL_Delay(2000);  // 等待ESP响应
    }
    
    esp_connected = 1;  // 设置连接状态
		OLED_Clear();
		OLED_PrintString(0, 0, "ConnectingOK");
}

// 发送烟花指令
void Send_Fire_Command(void)
{
    char send_cmd[] = "AT+CIPSEND=4\r\n";
    char fire_data[] = "fire";
    
    // 发送准备指令
    HAL_UART_Transmit(&huart1, (uint8_t*)send_cmd, strlen(send_cmd), 1000);
    HAL_Delay(500);
    
    // 发送数据
    HAL_UART_Transmit(&huart1, (uint8_t*)fire_data, strlen(fire_data), 1000);
    HAL_Delay(500);
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  MX_I2C1_Init();
  /* USER CODE BEGIN 2 */
  OLED_Init();
	OLED_Clear();
	OLED_PrintString(0, 0, "SYSTEM READY!");
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
		if(connect_flag)  // 需要连接
    {
			  OLED_Clear();
			  OLED_PrintString(0, 0, "Connecting");
        connect_flag = 0;
        ESP_Connect();
    }
    
    if(fire_flag)  // 需要发射
    {
			  OLED_Clear();
			  OLED_PrintString(0, 0, "Fire");
        fire_flag = 0;
        Send_Fire_Command();
    }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
