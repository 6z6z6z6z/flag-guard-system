import dayjs from 'dayjs';

export const formatDate = (date: string | Date | null | undefined): string => {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm');
};

export const isTrainingStarted = (startTime: string | Date): boolean => {
  return dayjs(startTime).isBefore(dayjs());
};

export const isTrainingPast = (endTime: string | Date | null | undefined): boolean => {
  if (!endTime) return false;
  return dayjs(endTime).isBefore(dayjs());
}; 