use std::error::Error;

pub fn parse_flag_value<'a>(args: &'a [&'a str], flag: &str) -> Option<&'a str> {
	let mut i = 0usize;
	while i + 1 < args.len() {
		if args[i] == flag {
			return Some(args[i + 1]);
		}
		i += 1;
	}
	None
}

pub fn parse_f64_flag(args: &[&str], flag: &str, default: f64) -> Result<f64, Box<dyn Error>> {
	match parse_flag_value(args, flag) {
		Some(raw) => Ok(raw.parse::<f64>()?),
		None => Ok(default),
	}
}

pub fn parse_list_flag(args: &[&str], flag: &str) -> Vec<String> {
	parse_flag_value(args, flag)
		.map(|raw| {
			raw
				.split(',')
				.map(str::trim)
				.filter(|s| !s.is_empty())
				.map(ToString::to_string)
				.collect::<Vec<String>>()
		})
		.unwrap_or_default()
}

pub fn parse_f64_list_flag(args: &[&str], flag: &str) -> Result<Vec<f64>, Box<dyn Error>> {
	let values = parse_list_flag(args, flag);
	let mut out = Vec::new();
	for value in values {
		out.push(value.parse::<f64>()?);
	}
	Ok(out)
}

pub fn parse_usize_flag(args: &[&str], flag: &str, default: usize) -> Result<usize, Box<dyn Error>> {
	match parse_flag_value(args, flag) {
		Some(raw) => Ok(raw.parse::<usize>()?),
		None => Ok(default),
	}
}

pub fn parse_usize_list_flag(args: &[&str], flag: &str) -> Result<Vec<usize>, Box<dyn Error>> {
	let values = parse_list_flag(args, flag);
	let mut out = Vec::new();
	for value in values {
		out.push(value.parse::<usize>()?);
	}
	Ok(out)
}
