import React, { useRef, useEffect } from 'react';
import { useTheme } from '@mui/material/styles';
import { Box, Paper } from '@mui/material';
import Editor from '@monaco-editor/react';

const PromptMonacoEditor = ({ value, onChange, readOnly = false }) => {
  const theme = useTheme();
  const editorRef = useRef(null);
  const debounceTimeout = useRef(null);

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;

    // Configure markdown language features
    monaco.languages.setLanguageConfiguration('markdown', {
      wordPattern: /(-?\d*\.\d\w*)|([^\`\~\!\@\#\%\^\&\*\(\)\-\=\+\[\{\]\}\\\|\;\:\'\"\,\.\<\>\/\?\s]+)/g,
    });

    // Add custom validation for {text} placeholder
    monaco.editor.onDidChangeModelContent(() => {
      const model = editor.getModel();
      const content = model.getValue();
      const markers = [];

      if (!content.includes('{text}')) {
        // Add error marker for missing placeholder
        markers.push({
          severity: monaco.MarkerSeverity.Error,
          message: 'Prompt must contain {text} placeholder',
          startLineNumber: 1,
          startColumn: 1,
          endLineNumber: 1,
          endColumn: 1,
        });
      }

      monaco.editor.setModelMarkers(model, 'promptValidator', markers);
    });
  };

  const handleEditorChange = (newValue) => {
    // Debounce the onChange callback
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    debounceTimeout.current = setTimeout(() => {
      onChange(newValue);
    }, 300);
  };

  useEffect(() => {
    return () => {
      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }
    };
  }, []);

  return (
    <Paper sx={{ mb: 2, overflow: 'hidden' }}>
      <Box sx={{ height: '500px' }}>
        <Editor
          height="100%"
          language="markdown"
          theme={theme.palette.mode === 'dark' ? 'vs-dark' : 'vs-light'}
          value={value}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: true },
            wordWrap: 'on',
            lineNumbers: 'on',
            fontSize: 14,
            fontFamily: 'Consolas, Monaco, monospace',
            scrollBeyondLastLine: false,
            readOnly: readOnly,
            automaticLayout: true,
            tabSize: 2,
            renderWhitespace: 'selection',
            folding: true,
            lineDecorationsWidth: 10,
            lineNumbersMinChars: 3,
            glyphMargin: true,
            padding: { top: 10, bottom: 10 },
          }}
        />
      </Box>
    </Paper>
  );
};

export default PromptMonacoEditor;
