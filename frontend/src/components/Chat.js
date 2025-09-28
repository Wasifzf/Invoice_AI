import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Paper, List, ListItem, ListItemText } from '@mui/material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Chat = ({ token }) => {
  const [messages, setMessages] = useState([
    // Optionally, add a system prompt here for display
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', content: input };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);
    try {
      const res = await axios.post(
        '/chatbot/',
        { messages: newMessages },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      setMessages([...newMessages, { role: 'assistant', content: res.data.response }]);
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: 'Error: Could not get response.' }]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Box maxWidth={600} mx="auto" mt={4}>
      <Typography variant="h5" mb={2}>Invoice Chatbot</Typography>
      <Paper sx={{ minHeight: 300, maxHeight: 400, overflow: 'auto', mb: 2, p: 2 }}>
        <List>
          {messages.map((msg, idx) => (
            <ListItem key={idx} alignItems={msg.role === 'user' ? 'right' : 'left'}>
              <ListItemText
                primary={
                  msg.role === 'assistant' ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )
                }
                sx={{ textAlign: msg.role === 'user' ? 'right' : 'left' }}
                primaryTypographyProps={{
                  color: msg.role === 'user' ? 'primary' : 'secondary',
                  fontWeight: msg.role === 'user' ? 600 : 400
                }}
              />
            </ListItem>
          ))}
        </List>
      </Paper>
      <Box display="flex" gap={2}>
        <TextField
          label="Type your message..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          fullWidth
          multiline
          minRows={1}
          maxRows={4}
          disabled={loading}
        />
        <Button variant="contained" onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </Button>
      </Box>
    </Box>
  );
};

export default Chat; 