import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import Login from './components/Login';
import Chat from './components/Chat';
import Invoices from './components/Invoices';
import FileUpload from './components/FileUpload';
import { AppBar, Toolbar, Button, Box } from '@mui/material';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');

  useEffect(() => {
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
  }, [token]);

  const logout = () => {
    setToken('');
    localStorage.removeItem('token');
  };

  return (
    <Router>
      <AppBar position="static">
        <Toolbar>
          <Box flexGrow={1}>
            <Button color="inherit" component={Link} to="/chat">Chat</Button>
            <Button color="inherit" component={Link} to="/invoices">Invoices</Button>
            <Button color="inherit" component={Link} to="/upload">Upload</Button>
          </Box>
          {token ? (
            <Button color="inherit" onClick={logout}>Logout</Button>
          ) : (
            <Button color="inherit" component={Link} to="/login">Login</Button>
          )}
        </Toolbar>
      </AppBar>
      <Routes>
        <Route path="/login" element={<Login setToken={setToken} />} />
        <Route path="/chat" element={token ? <Chat token={token} /> : <Navigate to="/login" />} />
        <Route path="/invoices" element={token ? <Invoices token={token} /> : <Navigate to="/login" />} />
        <Route path="/upload" element={token ? <FileUpload token={token} /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to={token ? "/chat" : "/login"} />} />
      </Routes>
    </Router>
  );
}

export default App;
