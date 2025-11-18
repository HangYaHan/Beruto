# Global Block Design

首先建立回测系统，回测系统应该实现以下接口：
装载股票数据，即向Fetcher发送Data_Request，装载返回值Data_Response；装载策略，得到结果。

# Modules

## Module -- Data

### Interface

> Data_Request --> [Fetcher] --> Data_Response

Input: Data_Request
Output: Data_Response

### Functionality

对于不同的数据源（Data_Source），设计独立的适配器（Adapter_i）负责数据获取与初步规范化，最终将数据存储到本地统一存储（Local_Uniform_Storage）中，供上层模块调用。需要强调的是，保存的数据格式必须具有统一的格式。fetcher提供了统一的接口供上层调用，它会先查询传入参数对应的数据是否已保存在本地缓存，若未命中则调用对应适配器（Adapter_i）获取数据并写入缓存。