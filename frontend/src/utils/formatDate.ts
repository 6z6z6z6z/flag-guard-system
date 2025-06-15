import dayjs from 'dayjs';

// 用于训练的开始和结束时间（已经是北京时间）
export const formatDate = (date: string | Date | null | undefined): string => {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm');
};

// 用于报名时间（需要从UTC转换为北京时间）
export const formatRegistrationTime = (date: string | Date | null | undefined): string => {
  if (!date) return '';
  return dayjs(date).add(8, 'hour').format('YYYY-MM-DD HH:mm');
};

export const isTrainingStarted = (startTime: string | Date): boolean => {
  return dayjs(startTime).isBefore(dayjs());
};

export const isTrainingPast = (endTime: string | Date | null | undefined): boolean => {
  if (!endTime) return false;
  return dayjs(endTime).isBefore(dayjs());
}; 