import { AlertTriangle } from "lucide-react";
import { Button, Modal } from "./ui.jsx";

export default function ConfirmDialog({
  title = "Are you sure?",
  description,
  confirmLabel = "Confirm",
  onCancel,
  onConfirm,
  busy = false,
  destructive = false,
}) {
  return (
    <Modal title={title} onClose={onCancel}>
      <div className="confirm-dialog">
        {destructive && <span className="confirm-dialog__icon"><AlertTriangle size={20} /></span>}
        <p>{description}</p>
        <div className="modal__actions">
          <Button type="button" variant="secondary" onClick={onCancel} disabled={busy}>Cancel</Button>
          <Button type="button" variant={destructive ? "danger" : "primary"} onClick={onConfirm} disabled={busy}>
            {busy ? "Working…" : confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
