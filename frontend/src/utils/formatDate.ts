import dayjs from 'dayjs';

// 用于训练的开始和结束时间（已经是北京时间）
export const formatDate = (date: string | Date | null | undefined): string => {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm');
};

// 用于报名时间（需要从UTC转换为北京时间）
export const formatRegistrationTime = (date: string | Date | null | undefined): string => {
  if (!date) return '';
  
  // 先尝试解析日期
  let dateObj;
  if (typeof date === 'string') {
    // 如果是字符串，确保处理可能的UTC格式（带Z或不带）
    if (date.endsWith('Z')) {
      // 已经是UTC格式
      dateObj = dayjs(date).add(8, 'hour');
    } else if (date.includes('T') && date.includes('.')) {
      // 可能是不带Z的ISO格式，假设为UTC
      dateObj = dayjs(date).add(8, 'hour');
    } else {
      // 其他格式，可能已经是本地时间
      const parsed = dayjs(date);
      // 检查字符串是否像MySQL的DATETIME格式
      if (date.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)) {
        // MySQL DATETIME默认没有时区信息，假设为UTC
        dateObj = parsed.add(8, 'hour');
      } else {
        dateObj = parsed;
      }
    }
  } else {
    // 如果是Date对象，假设为本地时间
    dateObj = dayjs(date);
  }
  
  return dateObj.format('YYYY-MM-DD HH:mm');
};

export const isTrainingStarted = (startTime: string | Date): boolean => {
  return dayjs(startTime).isBefore(dayjs());
};

export const isTrainingPast = (endTime: string | Date | null | undefined): boolean => {
  if (!endTime) return false;
  return dayjs(endTime).isBefore(dayjs());
}; 