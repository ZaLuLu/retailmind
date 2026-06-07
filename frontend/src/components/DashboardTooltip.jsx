import { useState, useRef, useEffect } from 'react';
import './DashboardTooltip.css';

export default function DashboardTooltip({ title, content }) {
  const [isOpen, setIsOpen] = useState(false);
  const tooltipRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (e) => {
      if (tooltipRef.current && !tooltipRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className="dashboard-tooltip-container" ref={tooltipRef}>
      <button 
        type="button" 
        className="tooltip-trigger" 
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Help for ${title}`}
      >
        ?
      </button>
      {isOpen && (
        <div className="tooltip-popup-bubble">
          <h4 className="tooltip-title">{title}</h4>
          <p className="tooltip-content">{content}</p>
        </div>
      )}
    </div>
  );
}
