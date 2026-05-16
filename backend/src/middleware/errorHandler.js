// ParkiPay — Global Express error handler
function errorHandler(err, req, res, _next) {
  const status = err.status || err.statusCode || 500;
  const detail = err.message || 'Internal server error.';

  if (process.env.NODE_ENV !== 'production') {
    console.error(err);
  }

  res.status(status).json({ error: err.code || 'server_error', detail });
}

module.exports = errorHandler;
