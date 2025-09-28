import React, { useEffect, useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, CircularProgress, Box } from '@mui/material';
import axios from 'axios';

const Invoices = ({ token }) => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInvoices = async () => {
      try {
        const res = await axios.get('/invoices/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setInvoices(res.data);
      } catch (err) {
        setInvoices([]);
      }
      setLoading(false);
    };
    fetchInvoices();
  }, [token]);

  if (loading) return <Box display="flex" justifyContent="center" mt={4}><CircularProgress /></Box>;

  return (
    <Box maxWidth={800} mx="auto" mt={4}>
      <Typography variant="h5" mb={2}>Your Invoices</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Invoice #</TableCell>
              <TableCell>Vendor</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {invoices.map(inv => (
              <TableRow key={inv.id}>
                <TableCell>{inv.invoice_number || 'N/A'}</TableCell>
                <TableCell>{inv.vendor}</TableCell>
                <TableCell>{inv.date}</TableCell>
                <TableCell>${inv.amount.toFixed(2)}</TableCell>
                <TableCell>{inv.status}</TableCell>
                <TableCell>{inv.category || 'N/A'}</TableCell>
                <TableCell>{inv.description}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Invoices; 