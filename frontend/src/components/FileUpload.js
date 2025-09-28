import React, { useState } from 'react';
import { Box, Button, Typography, Alert, CircularProgress, Paper } from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import axios from 'axios';

const FileUpload = ({ token }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
      if (allowedTypes.includes(selectedFile.type)) {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please select a valid file (PDF, JPG, PNG, or WebP)');
        setFile(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/upload-invoice/', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
      setFile(null);
      // Reset file input
      document.getElementById('file-input').value = '';
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box maxWidth={600} mx="auto" mt={4}>
      <Typography variant="h5" mb={2}>Upload Invoice</Typography>
      
      <Paper sx={{ p: 3, mb: 2 }}>
        <input
          id="file-input"
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.webp"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        
        <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
          <Button
            variant="outlined"
            component="label"
            startIcon={<CloudUpload />}
            disabled={uploading}
            onClick={() => document.getElementById('file-input').click()}
          >
            Select Invoice File
          </Button>
          
          {file && (
            <Typography variant="body2" color="text.secondary">
              Selected: {file.name}
            </Typography>
          )}
          
          {file && (
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={uploading}
              startIcon={uploading ? <CircularProgress size={20} /> : null}
            >
              {uploading ? 'Processing...' : 'Upload & Extract Data'}
            </Button>
          )}
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" mb={2}>Extraction Results</Typography>
          <Box>
            <Typography><strong>Invoice Number:</strong> {result.extracted_data.invoice_number || 'N/A'}</Typography>
            <Typography><strong>Vendor:</strong> {result.extracted_data.vendor || 'N/A'}</Typography>
            <Typography><strong>Customer:</strong> {result.extracted_data.customer || 'N/A'}</Typography>
            <Typography><strong>Date:</strong> {result.extracted_data.date || 'N/A'}</Typography>
            <Typography><strong>Total Amount:</strong> ${result.extracted_data.total || 0}</Typography>
            <Typography><strong>Items Count:</strong> {result.extracted_data.items_count}</Typography>
            <Typography><strong>Status:</strong> Invoice added to your database</Typography>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default FileUpload; 