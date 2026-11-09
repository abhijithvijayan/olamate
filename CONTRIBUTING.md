# Contributing

Thanks for your interest in OlaMate! This project is open to contributions from anyone with an Ola S1 Pro Gen 1.

## Compatibility

OlaMate currently supports the **Ola S1 Pro Gen 1 only**. Other Ola models (Gen 2, S1 X, S1 Air) have different CAN bus layouts and gRPC services. If you own a different model and want to add support, open an issue first to discuss the approach.

## Getting started

```bash
git clone <your-fork-url> && cd olamate
make setup
make test
```

## Making changes

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run `make test` to verify nothing breaks
4. Open a pull request

## CAN signal definitions

The signal definitions in `collector/can_decoder.py` are derived from the community CAN database extracted from the REA (Ride Experience App). If you're adding or correcting signals:

- Verify against a real scooter whenever possible
- Include the CAN ID, signal name, bit position, scaling and offset
- Note how you verified the value (e.g., "compared dashboard SOC display to decoded value")

## Areas where help is welcome

- Testing on different Gen 1 firmware versions (MoveOS 3.x vs 4.x)
- Additional CAN signal decoding (there are 226 messages, we decode 18)
- Dashboard improvements and new visualizations
- Charge session detection (currently only ride sessions are auto-detected)
- Documentation and setup guides for different platforms

## Code style

- Python: standard conventions, type hints where practical
- TypeScript: strict mode
- No comments unless the WHY is non-obvious
- Run tests before submitting
