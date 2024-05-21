import winston, { transports } from "winston";

// 创建一个新的 Winston 日志记录器
const logger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message }) => {
      return `${timestamp} -- ${level} -- ${message}`;
    }),
  ),
  transports: [new transports.Console()],
});

export default logger;
