import React, { useState } from 'react';

const MainContent = () => {
  const [aiText, setAiText] = useState('');
  const [loading, setLoading] = useState(false);
  const [chapterContent, setChapterContent] = useState('');
  const [chapterLoading, setChapterLoading] = useState(false);
  const memoryId = 'test_memory';

  // 加载章节内容
  React.useEffect(() => {
    setChapterLoading(true);
    fetch(`http://localhost:8000/memory/${memoryId}`)
      .then(res => res.json())
      .then(data => {
        setChapterContent(data.text || '');
      })
      .catch(() => setChapterContent(''))
      .finally(() => setChapterLoading(false));
  }, []);

  // 保存章节内容
  const handleSaveChapter = async () => {
    setChapterLoading(true);
    try {
      await fetch('http://localhost:8000/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory_id: memoryId, text: chapterContent })
      });
      alert('章节内容已保存！');
    } catch {
      alert('保存失败，请检查后端服务');
    }
    setChapterLoading(false);
  };

  const handleChapterChange = e => setChapterContent(e.target.value);

  const handleAIGenerate = async () => {
    setLoading(true);
    setAiText('');
    try {
      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory_id: 'test_memory', prompt: '写一个人物介绍。' })
      });
      const data = await res.json();
      setAiText(data.text || 'AI未返回内容');
    } catch (e) {
      setAiText('请求失败，请检查后端服务');
    }
    setLoading(false);
  };

  return (
    <div className="flex-1 overflow-y-auto bg-white">
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* 标题输入 */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Novel Title"
            className="w-full text-3xl font-bold border-none focus:outline-none focus:ring-0 placeholder-gray-300"
          />
          <input
            type="text"
            placeholder="Subtitle or tagline"
            className="w-full text-xl text-gray-500 border-none focus:outline-none focus:ring-0 placeholder-gray-300 mt-2"
          />
        </div>

        {/* 章节区域 */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Chapter 1: The Beginning</h2>
            <div className="flex space-x-2">
              <button className="p-1 text-gray-500 hover:text-gray-700">
                <i className="fas fa-cog"></i>
              </button>
              <button className="p-1 text-gray-500 hover:text-gray-700">
                <i className="fas fa-trash-alt"></i>
              </button>
            </div>
          </div>

          {/* 编辑内容 */}
          <div className="editor-content">
            <textarea
              className="w-full h-48 p-3 border border-gray-200 rounded mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-vertical"
              placeholder="请在此输入章节内容..."
              value={chapterContent}
              onChange={handleChapterChange}
              disabled={chapterLoading}
            />
            <div className="flex items-center space-x-2 mb-4">
              <button
                className="px-4 py-2 bg-green-600 text-white rounded-md font-medium hover:bg-green-700 flex items-center disabled:opacity-60"
                onClick={handleSaveChapter}
                disabled={chapterLoading}
              >
                <i className="fas fa-save mr-2"></i> {chapterLoading ? '保存中...' : '保存章节'}
              </button>
            </div>
            {/* AI 建议示例 */}
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
              <p className="text-sm text-blue-700">
                <span className="font-semibold">AI Suggestion:</span> Consider adding more sensory
                details about the rain to enhance atmosphere.
              </p>
            </div>
            {/* AI生成内容展示区 */}
            {aiText && (
              <div className="bg-gray-50 border-l-4 border-indigo-400 p-4 my-2 text-gray-900 whitespace-pre-line">
                <b>AI生成：</b>
                <div>{aiText}</div>
              </div>
            )}
            <div className="flex items-center space-x-2 mt-4">
              <button
                className="px-4 py-2 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700 flex items-center disabled:opacity-60"
                onClick={handleAIGenerate}
                disabled={loading}
              >
                <i className="fas fa-magic mr-2"></i> {loading ? '生成中...' : 'AI生成内容'}
              </button>
            </div>
            {/* 继续内容... */}
            {/* TODO: 更多段落和交互元素 */}
          </div>
        </div>

        {/* 新章节按钮 */}
        <div className="border-t border-gray-200 pt-6">
          <button className="px-4 py-2 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700 flex items-center">
            <i className="fas fa-plus mr-2"></i> Add New Chapter
          </button>
        </div>
      </div>
    </div>
  );
};

export default MainContent;
