"""Arquimedes fine-tuning package — dataset prep, training, eval.

The heavy lifting (training) runs in ``train_lora.ipynb`` on a GPU host.
The other modules (``dataset_prep``, ``eval``) can run on CPU to
prepare inputs and evaluate a trained adapter.
"""
