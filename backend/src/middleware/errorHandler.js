// ParkiPay — Global Express error handler
// Must be the LAST app.use() call in app.js.
// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, _next) {
  const status = err.status || err.statusCode || 500;
  const code   = err.code   || 'server_error';
  const detail = err.message || 'An unexpected error occurred.';

  // In development, log the full stack for easier debugging
  if (process.env.NODE_ENV !== 'production') {
    console.error('[ErrorHandler]', err);
  }

  // Never leak stack traces to clients in production
  res.status(status).json({ error: code, detail });
}

module.exports = errorHandler;
