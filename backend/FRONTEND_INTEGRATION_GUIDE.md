# Frontend Integration Guide

This guide shows how to integrate the enhanced chatbot features with your frontend.

## 🌐 **Supported Languages**

Your chatbot now supports 4 languages:
- **Burmese** (မြန်မာ) - Code: `my`
- **English** - Code: `en`
- **Chinese** (中文) - Code: `zh`
- **Japanese** (日本語) - Code: `ja`

## 📡 **API Endpoints**

### **Get Supported Languages**
```javascript
GET /languages
```
Response:
```json
[
  {"code": "my", "name": "Burmese", "native_name": "မြန်မာ"},
  {"code": "en", "name": "English", "native_name": "English"},
  {"code": "zh", "name": "Chinese", "native_name": "中文"},
  {"code": "ja", "name": "Japanese", "native_name": "日本語"}
]
```

### **Chat History Management**

#### **Get All Conversations**
```javascript
GET /chat/history/{user_id}
```

#### **Get Specific Conversation**
```javascript
GET /chat/history/{conversation_id}
```

#### **Delete Conversation**
```javascript
DELETE /chat/history/{conversation_id}
```

#### **Update Chat Title**
```javascript
PUT /chat/history/{conversation_id}/title
Content-Type: application/json

{
  "title": "New Chat Title"
}
```

## 🎨 **Frontend Implementation Examples**

### **1. Chat History List with Edit Button**

```html
<div class="chat-history">
  <div v-for="conversation in conversations" :key="conversation.id" class="conversation-item">
    <div class="conversation-header">
      <h3 v-if="!conversation.editing" @click="startEdit(conversation)">
        {{ conversation.topic }}
      </h3>
      <input 
        v-if="conversation.editing" 
        v-model="conversation.newTitle"
        @blur="saveTitle(conversation)"
        @keyup.enter="saveTitle(conversation)"
        @keyup.escape="cancelEdit(conversation)"
        class="title-input"
        maxlength="100"
      />
      <div class="conversation-actions">
        <button @click="startEdit(conversation)" class="edit-btn" title="Edit Title">
          ✏️
        </button>
        <button @click="deleteConversation(conversation.id)" class="delete-btn" title="Delete">
          🗑️
        </button>
      </div>
    </div>
  </div>
</div>
```

### **2. JavaScript Functions**

```javascript
// Edit title functionality
async function startEdit(conversation) {
  conversation.editing = true;
  conversation.newTitle = conversation.topic;
}

async function cancelEdit(conversation) {
  conversation.editing = false;
  conversation.newTitle = '';
}

async function saveTitle(conversation) {
  if (!conversation.newTitle.trim()) {
    alert('Title cannot be empty');
    return;
  }
  
  try {
    const response = await fetch(`/chat/history/${conversation.id}/title`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: conversation.newTitle.trim()
      })
    });
    
    if (response.ok) {
      conversation.topic = conversation.newTitle.trim();
      conversation.editing = false;
    } else {
      const error = await response.json();
      alert(`Error: ${error.message}`);
    }
  } catch (error) {
    console.error('Error updating title:', error);
    alert('Failed to update title');
  }
}

// Delete conversation functionality
async function deleteConversation(conversationId) {
  if (!confirm('Are you sure you want to delete this conversation?')) {
    return;
  }
  
  try {
    const response = await fetch(`/chat/history/${conversationId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      // Remove from UI
      conversations = conversations.filter(c => c.id !== conversationId);
    } else {
      const error = await response.json();
      alert(`Error: ${error.message}`);
    }
  } catch (error) {
    console.error('Error deleting conversation:', error);
    alert('Failed to delete conversation');
  }
}
```

### **3. CSS Styling**

```css
.conversation-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 10px 0;
  padding: 15px;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conversation-header h3 {
  margin: 0;
  cursor: pointer;
  flex: 1;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.conversation-header h3:hover {
  background-color: #f0f0f0;
}

.title-input {
  flex: 1;
  padding: 5px;
  border: 2px solid #007bff;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
}

.conversation-actions {
  display: flex;
  gap: 10px;
}

.edit-btn, .delete-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.edit-btn:hover {
  background-color: #e3f2fd;
}

.delete-btn:hover {
  background-color: #ffebee;
}
```

### **4. Language Detection Display**

```javascript
// Show detected language in chat
function displayLanguageInfo(detectedLanguage) {
  const languageNames = {
    'my': 'မြန်မာ',
    'en': 'English',
    'zh': '中文',
    'ja': '日本語'
  };
  
  const languageDisplay = languageNames[detectedLanguage] || 'Unknown';
  console.log(`Detected language: ${languageDisplay}`);
  
  // You can show this in your UI
  document.getElementById('language-indicator').textContent = 
    `Language: ${languageDisplay}`;
}
```

## 🔧 **Testing the Features**

### **Test Language Support:**
1. Send messages in Burmese: "မင်္ဂလာပါ"
2. Send messages in English: "Hello, how are you?"
3. Send messages in Chinese: "你好，你好吗？"
4. Send messages in Japanese: "こんにちは、元気ですか？"

### **Test Edit Functionality:**
1. Create a new chat conversation
2. Click on the conversation title to edit
3. Type a new title and press Enter
4. Verify the title is updated

### **Test Delete Functionality:**
1. Click the delete button on a conversation
2. Confirm the deletion
3. Verify the conversation is removed

## 📝 **Notes**

- The chatbot automatically detects the input language
- Responses will be in the same language as the input
- Title editing updates the first user message (workaround for database structure)
- All endpoints include proper error handling
- Maximum title length is 100 characters

## 🚀 **Ready to Use**

Your backend now supports:
- ✅ 4 languages (Burmese, English, Chinese, Japanese)
- ✅ Automatic language detection
- ✅ Language-specific responses
- ✅ Chat title editing
- ✅ Conversation deletion
- ✅ Comprehensive error handling

The frontend can now implement edit buttons and language indicators using these endpoints!
