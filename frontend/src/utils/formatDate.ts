import dayjs from 'dayjs';

/**
 * 格式化时间为显示格式（输入假设为北京时间）
 * @param date 时间字符串或Date对象
 * @returns 格式化后的时间字符串
 */
export const formatDate = (date: string | Date | null | undefined): string => {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm');
};

/**
 * 格式化报名时间（从后端返回的时间）
 * @param date 时间字符串或Date对象
 * @returns 格式化后的时间字符串
 */
export const formatRegistrationTime = (date: string | Date | null | undefined): string => {
  if (!date) return '';
  
  try {
    // 直接使用dayjs解析时间，它会正确处理时区信息
    const parsedTime = dayjs(date);
    return parsedTime.format('YYYY-MM-DD HH:mm:ss');
  } catch (error) {
    console.error('时间格式化失败:', date, error);
    return '时间格式错误';
  }
};

/**
 * 判断训练是否已开始（基于北京时间）
 * @param startTime 开始时间
 * @returns 是否已开始
 */
export const isTrainingStarted = (startTime: string | Date): boolean => {
  return dayjs(startTime).isBefore(dayjs());
};

/**
 * 判断训练是否已结束（基于北京时间）
 * @param endTime 结束时间
 * @returns 是否已结束
 */
export const isTrainingPast = (endTime: string | Date | null | undefined): boolean => {
  if (!endTime) return false;
  return dayjs(endTime).isBefore(dayjs());
};

/**
 * 格式化时间范围显示
 * @param start 开始时间
 * @param end 结束时间
 * @returns 格式化的时间范围
 */
export const formatDateTimeRange = (start: string, end: string): string => {
  if (!start) return 'N/A';
  
  // 直接使用dayjs解析时间，它会正确处理时区信息
  const startDate = dayjs(start);
  const startDateTime = startDate.format('YYYY-MM-DD HH:mm');

  if (!end) {
    return startDateTime;
  }

  const endDate = dayjs(end);
  const endTime = endDate.format('HH:mm');

  return `${startDateTime} - ${endTime}`;
};

/**
 * 将前端输入的时间转换为发送给后端的格式
 * 前端输入的时间就是北京时间，直接格式化不添加时区信息
 * 让后端将其视为北京时间处理
 * @param date Date对象或时间字符串
 * @returns ISO格式的时间字符串（不含时区信息）
 */
export const formatTimeForBackend = (date: Date | string): string => {
  if (!date) return '';
  
  // 直接格式化，不添加任何时区信息
  // 让后端将其视为北京时间
  if (typeof date === 'string') {
    return dayjs(date).format('YYYY-MM-DDTHH:mm:ss');
  }
  
  // Date对象直接格式化，不做任何时区转换
  return dayjs(date).format('YYYY-MM-DDTHH:mm:ss');
}; 