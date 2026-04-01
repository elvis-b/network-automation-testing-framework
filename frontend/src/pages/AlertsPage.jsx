import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Error as CriticalIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as AckIcon,
  Refresh as RefreshIcon,
  Done as ResolveIcon,
} from '@mui/icons-material';
import { alertsApi } from '../services/api';

// Severity icon component
function SeverityIcon({ severity }) {
  switch (severity) {
    case 'critical':
      return <CriticalIcon color="error" />;
    case 'warning':
      return <WarningIcon color="warning" />;
    default:
      return <InfoIcon color="info" />;
  }
}

function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('');
  const [tabValue, setTabValue] = useState(0); // 0 = active, 1 = acknowledged
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (severityFilter) params.severity = severityFilter;
      params.acknowledged = tabValue === 1;
      
      const response = await alertsApi.getAll(params);
      setAlerts(response.data.alerts || []);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
      setError('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [severityFilter, tabValue]);

  const handleAcknowledge = async (alert) => {
    try {
      await alertsApi.acknowledge(alert.id);
      fetchAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolve = async (alert) => {
    try {
      await alertsApi.resolve(alert.id);
      fetchAlerts();
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const handleAlertClick = (alert) => {
    setSelectedAlert(alert);
    setDialogOpen(true);
  };

  const activeCount = alerts.filter(a => !a.acknowledged).length;
  const criticalCount = alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4" fontWeight={700}>
            Alerts
          </Typography>
          {criticalCount > 0 && (
            <Chip
              label={`${criticalCount} Critical`}
              color="error"
              size="small"
            />
          )}
        </Box>
        <Tooltip title="Refresh">
          <IconButton onClick={fetchAlerts} data-testid="refresh-btn">
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Tabs and Filters */}
      <Card sx={{ mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label={`Active (${activeCount})`} data-testid="tab-active" />
            <Tab label="Acknowledged" data-testid="tab-acknowledged" />
          </Tabs>
        </Box>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Severity</InputLabel>
              <Select
                value={severityFilter}
                label="Severity"
                onChange={(e) => setSeverityFilter(e.target.value)}
                data-testid="severity-filter"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
                <MenuItem value="warning">Warning</MenuItem>
                <MenuItem value="info">Info</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Alerts List */}
      <Card>
        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress data-testid="loading" />
            </Box>
          ) : alerts.length === 0 ? (
            <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
              No alerts found
            </Typography>
          ) : (
            <List data-testid="alert-list">
              {alerts.map((alert) => (
                <ListItem
                  key={alert.id}
                  data-testid={`alert-${alert.id}`}
                  className="alert-item"
                  sx={{
                    borderRadius: 2,
                    mb: 1,
                    bgcolor: alert.severity === 'critical' 
                      ? 'rgba(255, 82, 82, 0.1)' 
                      : alert.severity === 'warning'
                      ? 'rgba(255, 171, 64, 0.1)'
                      : 'rgba(64, 196, 255, 0.05)',
                    border: '1px solid',
                    borderColor: alert.severity === 'critical' 
                      ? 'rgba(255, 82, 82, 0.3)' 
                      : alert.severity === 'warning'
                      ? 'rgba(255, 171, 64, 0.3)'
                      : 'rgba(64, 196, 255, 0.2)',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: alert.severity === 'critical' 
                        ? 'rgba(255, 82, 82, 0.15)' 
                        : alert.severity === 'warning'
                        ? 'rgba(255, 171, 64, 0.15)'
                        : 'rgba(64, 196, 255, 0.1)',
                    },
                  }}
                  onClick={() => handleAlertClick(alert)}
                >
                  <ListItemIcon>
                    <SeverityIcon severity={alert.severity} />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography fontWeight={500} className="alert-message">
                        {alert.message}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        <Typography variant="body2" color="text.secondary" component="span">
                          {alert.device_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" component="span" sx={{ mx: 1 }}>
                          •
                        </Typography>
                        <Typography variant="body2" color="text.secondary" component="span">
                          {new Date(alert.timestamp).toLocaleString()}
                        </Typography>
                        {alert.acknowledged && (
                          <>
                            <Typography variant="body2" color="text.secondary" component="span" sx={{ mx: 1 }}>
                              •
                            </Typography>
                            <Typography variant="body2" color="success.main" component="span">
                              Acknowledged by {alert.acknowledged_by}
                            </Typography>
                          </>
                        )}
                      </Box>
                    }
                  />
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={alert.severity}
                      size="small"
                      color={
                        alert.severity === 'critical' ? 'error' :
                        alert.severity === 'warning' ? 'warning' : 'info'
                      }
                    />
                    {!alert.acknowledged && (
                      <Tooltip title="Acknowledge">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAcknowledge(alert);
                          }}
                          data-testid={`ack-btn-${alert.id}`}
                          sx={{ color: 'success.main' }}
                        >
                          <AckIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    {alert.acknowledged && !alert.resolved && (
                      <Tooltip title="Resolve">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleResolve(alert);
                          }}
                          data-testid={`resolve-btn-${alert.id}`}
                          sx={{ color: 'primary.main' }}
                        >
                          <ResolveIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Alert Detail Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {selectedAlert && <SeverityIcon severity={selectedAlert.severity} />}
            Alert Details
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Message
                </Typography>
                <Typography>{selectedAlert.message}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Device
                </Typography>
                <Typography>{selectedAlert.device_name}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Severity
                </Typography>
                <Box>
                  <Chip
                    label={selectedAlert.severity}
                    size="small"
                    color={
                      selectedAlert.severity === 'critical' ? 'error' :
                      selectedAlert.severity === 'warning' ? 'warning' : 'info'
                    }
                  />
                </Box>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Type
                </Typography>
                <Typography>{selectedAlert.type}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Timestamp
                </Typography>
                <Typography>
                  {new Date(selectedAlert.timestamp).toLocaleString()}
                </Typography>
              </Box>
              {selectedAlert.acknowledged && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Acknowledged
                  </Typography>
                  <Typography>
                    By {selectedAlert.acknowledged_by} at {new Date(selectedAlert.acknowledged_at).toLocaleString()}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          {selectedAlert && !selectedAlert.acknowledged && (
            <Button
              variant="contained"
              color="success"
              onClick={() => {
                handleAcknowledge(selectedAlert);
                setDialogOpen(false);
              }}
            >
              Acknowledge
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default AlertsPage;

