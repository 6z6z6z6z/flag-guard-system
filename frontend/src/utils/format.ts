import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'

dayjs.extend(utc)

/**
 * 格式化日期时间，精确到秒，并进行UTC到CST (+8) 的转换
 * @param dateTime 日期时间字符串 (应为UTC时间)
 * @returns 格式化后的日期时间字符串
 */
export const formatDateTime = (dateTime: string | null | undefined): string => {
  if (!dateTime) return 'N/A'
  
  // 假设输入是UTC时间，转换为本地时间(东八区)并格式化
  const formattedTime = dayjs.utc(dateTime).local().format('YYYY-MM-DD HH:mm:ss')
  
  if (formattedTime === 'Invalid Date') {
    // 如果dayjs解析失败，尝试使用原生Date对象作为后备
    const date = new Date(dateTime)
    if (isNaN(date.getTime())) {
      return 'Invalid Date'
    }
    // 手动进行UTC+8的转换
    date.setHours(date.getHours() + 8)
    return date.toISOString().slice(0, 19).replace('T', ' ')
  }

  return formattedTime
} 