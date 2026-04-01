import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Button,
  Chip,
  TextField,
  InputAdornment,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { devicesApi } from '../services/api';

// Status chip colors
const statusColors = {
  active: 'success',
  inactive: 'error',
  maintenance: 'warning',
};

// Device type options
const deviceTypes = ['router', 'switch', 'firewall'];
const statusOptions = ['active', 'inactive', 'maintenance'];

function DevicesPage() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [deviceToDelete, setDeviceToDelete] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    ip_address: '',
    device_type: 'router',
    vendor: '',
    model: '',
    status: 'active',
    location: '',
  });
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchDevices = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      
      const response = await devicesApi.getAll(params);
      setDevices(response.data.devices || []);
    } catch (err) {
      console.error('Failed to fetch devices:', err);
      setError('Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, [search, statusFilter]);

  const handleOpenDialog = (device = null) => {
    if (device) {
      setEditingDevice(device);
      setFormData({
        name: device.name,
        ip_address: device.ip_address,
        device_type: device.device_type,
        vendor: device.vendor || '',
        model: device.model || '',
        status: device.status,
        location: device.location || '',
      });
    } else {
      setEditingDevice(null);
      setFormData({
        name: '',
        ip_address: '',
        device_type: 'router',
        vendor: '',
        model: '',
        status: 'active',
        location: '',
      });
    }
    setFormError('');
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingDevice(null);
    setFormError('');
  };

  const handleSaveDevice = async () => {
    setSaving(true);
    setFormError('');
    
    try {
      if (editingDevice) {
        await devicesApi.update(editingDevice.id, formData);
      } else {
        await devicesApi.create(formData);
      }
      handleCloseDialog();
      fetchDevices();
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to save device';
      setFormError(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteClick = (device) => {
    setDeviceToDelete(device);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    try {
      await devicesApi.delete(deviceToDelete.id);
      setDeleteDialogOpen(false);
      setDeviceToDelete(null);
      fetchDevices();
    } catch (err) {
      console.error('Failed to delete device:', err);
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Devices
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          data-testid="add-device-btn"
        >
          Add Device
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search devices..."
              size="small"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              data-testid="search-input"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color="action" />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 250 }}
            />
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
                data-testid="status-filter"
              >
                <MenuItem value="">All</MenuItem>
                {statusOptions.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Tooltip title="Refresh">
              <IconButton onClick={fetchDevices} data-testid="refresh-btn">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Device Table */}
      <Card>
        <TableContainer>
          <Table data-testid="device-table">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>IP Address</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Vendor</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Location</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <CircularProgress data-testid="loading" />
                  </TableCell>
                </TableRow>
              ) : devices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      No devices found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                devices.map((device) => (
                  <TableRow
                    key={device.id}
                    data-testid={`device-row-${device.id}`}
                    hover
                  >
                    <TableCell>
                      <Typography fontWeight={500}>{device.name}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography fontFamily="monospace">{device.ip_address}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={device.device_type} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>{device.vendor || '-'}</TableCell>
                    <TableCell>
                      <Chip
                        label={device.status}
                        size="small"
                        color={statusColors[device.status] || 'default'}
                      />
                    </TableCell>
                    <TableCell>{device.location || '-'}</TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(device)}
                          data-testid={`edit-btn-${device.id}`}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteClick(device)}
                          data-testid={`delete-btn-${device.id}`}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingDevice ? 'Edit Device' : 'Add New Device'}
        </DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2, mt: 1 }}>
              {formError}
            </Alert>
          )}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Device Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
              inputProps={{ 'data-testid': 'device-name-input' }}
            />
            <TextField
              label="IP Address"
              value={formData.ip_address}
              onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              required
              fullWidth
              placeholder="192.168.1.1"
              inputProps={{ 'data-testid': 'device-ip-input' }}
            />
            <FormControl fullWidth>
              <InputLabel>Device Type</InputLabel>
              <Select
                value={formData.device_type}
                label="Device Type"
                onChange={(e) => setFormData({ ...formData, device_type: e.target.value })}
                data-testid="device-type-select"
              >
                {deviceTypes.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Vendor"
              value={formData.vendor}
              onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
              fullWidth
            />
            <TextField
              label="Model"
              value={formData.model}
              onChange={(e) => setFormData({ ...formData, model: e.target.value })}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                label="Status"
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                data-testid="device-status-select"
              >
                {statusOptions.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Location"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSaveDevice}
            disabled={saving || !formData.name || !formData.ip_address}
            data-testid="save-device-btn"
          >
            {saving ? <CircularProgress size={20} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete device "{deviceToDelete?.name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleConfirmDelete}
            data-testid="confirm-delete-btn"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default DevicesPage;

