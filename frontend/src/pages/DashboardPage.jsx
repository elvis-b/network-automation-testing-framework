import { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  IconButton,
  Tooltip,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
} from '@mui/material';
import {
  Router as DevicesIcon,
  Warning as AlertIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  Refresh as RefreshIcon,
  Error as CriticalIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { devicesApi, alertsApi } from '../services/api';

// Stat Card Component
function StatCard({ title, value, icon, color, testId }) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h3" fontWeight={700} data-testid={testId}>
              {value}
            </Typography>
          </Box>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: `${color}.main`,
              opacity: 0.9,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

// Alert Severity Icon
function SeverityIcon({ severity }) {
  switch (severity) {
    case 'critical':
      return <CriticalIcon color="error" />;
    case 'warning':
      return <AlertIcon color="warning" />;
    default:
      return <InfoIcon color="info" />;
  }
}

function DashboardPage() {
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [devicesRes, alertsRes] = await Promise.all([
        devicesApi.getAll(),
        alertsApi.getAll({ acknowledged: false }),
      ]);
      setDevices(devicesRes.data.devices || []);
      setAlerts(alertsRes.data.alerts || []);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const activeDevices = devices.filter(d => d.status === 'active').length;
  const inactiveDevices = devices.filter(d => d.status !== 'active').length;
  const criticalAlerts = alerts.filter(a => a.severity === 'critical').length;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress data-testid="loading" />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Dashboard
        </Typography>
        <Tooltip title="Refresh">
          <IconButton onClick={fetchData} data-testid="refresh-btn">
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Devices"
            value={devices.length}
            icon={<DevicesIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="primary"
            testId="device-count"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Alerts"
            value={alerts.length}
            icon={<AlertIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="warning"
            testId="alert-count"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Devices"
            value={activeDevices}
            icon={<ActiveIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="success"
            testId="active-device-count"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Inactive Devices"
            value={inactiveDevices}
            icon={<InactiveIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="error"
            testId="inactive-device-count"
          />
        </Grid>
      </Grid>

      {/* Content Grid */}
      <Grid container spacing={3}>
        {/* Device List */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Recent Devices
              </Typography>
              <List data-testid="device-list">
                {devices.slice(0, 5).map((device) => (
                  <ListItem
                    key={device.id}
                    data-testid={`device-item-${device.id}`}
                    className="device-item"
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' },
                    }}
                  >
                    <ListItemIcon>
                      {device.status === 'active' ? (
                        <ActiveIcon color="success" />
                      ) : (
                        <InactiveIcon color="error" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={<span className="device-name">{device.name}</span>}
                      secondary={device.ip_address}
                      className="device-status"
                    />
                    <Chip
                      label={device.device_type}
                      size="small"
                      variant="outlined"
                    />
                  </ListItem>
                ))}
                {devices.length === 0 && (
                  <Typography color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    No devices found
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Alerts Panel */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6" fontWeight={600}>
                  Active Alerts
                </Typography>
                {criticalAlerts > 0 && (
                  <Chip
                    label={`${criticalAlerts} Critical`}
                    color="error"
                    size="small"
                  />
                )}
              </Box>
              <List data-testid="alert-panel">
                {alerts.slice(0, 5).map((alert) => (
                  <ListItem
                    key={alert.id}
                    data-testid={`alert-item-${alert.id}`}
                    className="alert-item"
                    data-severity={alert.severity}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      bgcolor: alert.severity === 'critical' 
                        ? 'rgba(255, 82, 82, 0.1)' 
                        : alert.severity === 'warning'
                        ? 'rgba(255, 171, 64, 0.1)'
                        : 'transparent',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' },
                    }}
                  >
                    <ListItemIcon>
                      <SeverityIcon severity={alert.severity} />
                    </ListItemIcon>
                    <ListItemText
                      primary={<span className="alert-message">{alert.message}</span>}
                      secondary={
                        <span className="alert-device">
                          {alert.device_name} • {new Date(alert.timestamp).toLocaleString()}
                        </span>
                      }
                    />
                    <Chip
                      label={alert.severity}
                      size="small"
                      color={
                        alert.severity === 'critical' ? 'error' :
                        alert.severity === 'warning' ? 'warning' : 'info'
                      }
                      className="alert-severity"
                    />
                  </ListItem>
                ))}
                {alerts.length === 0 && (
                  <Typography color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    No active alerts
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default DashboardPage;

