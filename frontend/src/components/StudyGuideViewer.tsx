import ReactMarkdown from 'react-markdown';
import type { InterviewGuide } from '../types/study';

interface StudyGuideViewerProps {
  guide: InterviewGuide;
}

export function StudyGuideViewer({ guide }: StudyGuideViewerProps) {
  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown>{guide.content_md}</ReactMarkdown>
    </div>
  );
}
