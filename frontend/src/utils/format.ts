import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'

dayjs.extend(utc)

/**
 * 格式化日期时间，精确到秒
 * @param dateTime 日期时间字符串
 * @returns 格式化后的日期时间字符串
 */
export const formatDateTime = (dateTime: string | null | undefined): string => {
  if (!dateTime) return 'N/A'
  
  try {
    let parsedTime = dayjs(dateTime);
    
    // 检查是否包含时区信息（+08:00），如果有则减去8小时的重复偏移
    if (typeof dateTime === 'string' && dateTime.includes('+08:00')) {
      // 如果包含+08:00，说明已经是北京时间的ISO格式，减去8小时的重复偏移
      parsedTime = parsedTime.subtract(8, 'hour');
    }
    
    const formattedTime = parsedTime.format('YYYY-MM-DD HH:mm:ss');
    
    if (formattedTime === 'Invalid Date') {
      console.warn('Invalid date format:', dateTime)
      return 'Invalid Date'
    }

    return formattedTime
  } catch (error) {
    console.error('Date formatting error:', dateTime, error)
    return 'Date Error'
  }
} 