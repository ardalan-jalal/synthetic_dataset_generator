"""
Text processing utilities for OCR dataset generation
"""

import re
from typing import List


def split_long_lines(text: str, max_length: int = 100) -> List[str]:
    """
    Split text into chunks at sentence boundaries for realistic line lengths

    Args:
        text: Input text to split
        max_length: Maximum characters per line

    Returns:
        List of text chunks, each <= max_length
    """
    if len(text) <= max_length:
        return [text]

    # Step 1: Try splitting on punctuation boundaries
    # Kurdish/Arabic punctuation: ، (comma), ؛ (semicolon), . ! ?
    sentences = re.split(r"([.!?،؛])\s+", text)

    chunks = []
    current_chunk = ""

    for part in sentences:
        # Check if it's a punctuation mark
        if part in ".!?،؛":
            current_chunk += part
        else:
            # If adding this would exceed max length, save current chunk
            if current_chunk and len(current_chunk) + len(part) + 1 > max_length:
                chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                current_chunk += (
                    (" " + part)
                    if current_chunk
                    and not current_chunk.endswith((".", "!", "?", "،", "؛"))
                    else part
                )

    # Add the last chunk
    if current_chunk and current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Step 2: CRITICAL - Validate and force-split any chunk still exceeding max_length
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_length:
            final_chunks.append(chunk)
        else:
            # Split on word boundaries
            final_chunks.extend(_force_split(chunk, max_length))

    # Fallback: if somehow still empty, hard split original text
    return (
        final_chunks
        if final_chunks
        else [text[i : i + max_length] for i in range(0, len(text), max_length)]
    )


def _force_split(text: str, max_length: int) -> List[str]:
    """Force split text on word boundaries"""
    words = text.split()
    chunks = []
    temp_line = ""

    for word in words:
        # Check if adding this word would exceed limit
        test_line = (temp_line + " " + word) if temp_line else word

        if len(test_line) <= max_length:
            temp_line = test_line
        else:
            # Save current line if it exists
            if temp_line:
                chunks.append(temp_line)
                temp_line = word
            else:
                # Single word exceeds max_length - hard split it
                chunks.append(word[:max_length])
                temp_line = word[max_length:]

    # Don't forget the last line
    if temp_line:
        chunks.append(temp_line)

    return (
        chunks
        if chunks
        else [text[i : i + max_length] for i in range(0, len(text), max_length)]
    )
